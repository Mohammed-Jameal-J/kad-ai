import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import assistant, auth, cart, catalog, crew, orders
from app.core.config import settings
from app.core.errors import ServiceError
from app.db.seed import init_db

# Without this, our "kadai.*" INFO logs (model timings, seed results) are silently dropped:
# uvicorn only configures its own loggers.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("kadai")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    added = init_db()
    logger.info("Database ready, seed added %s", added)
    yield


app = FastAPI(
    title=f"{settings.app_name} API",
    version="0.1.0",
    description="Product catalog and cart API. All prices are integer paise and are demonstration prices.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-Cart-Id"],
)


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    # ponytail: trusts Content-Length; chunked uploads without it slip through. Fine behind
    # a local dev server, add a streaming limit (or a reverse proxy limit) before going public.
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > settings.max_request_bytes:
        return JSONResponse({"detail": "Request body too large"}, status_code=413)
    return await call_next(request)


@app.exception_handler(ServiceError)
async def service_error_handler(_request: Request, exc: ServiceError):
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse({"detail": "Internal server error"}, status_code=500)


app.include_router(catalog.router)
app.include_router(cart.router)
app.include_router(assistant.router)
app.include_router(orders.router)
app.include_router(crew.router)
app.include_router(auth.router)
