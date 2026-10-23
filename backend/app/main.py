import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.ai.ollama import get_ollama
from app.ai.parser import llm_parse
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
    if settings.ollama_prewarm and settings.llm_provider == "ollama":
        threading.Thread(target=_prewarm, daemon=True).start()
    yield


def _prewarm():
    try:
        # A real parse, not just a load: Ollama then also caches the long system prompt (~500 tokens,
        # ~15 s to read on CPU), so the first customer message is as fast as later ones.
        llm_parse(get_ollama(), "hello", [])
        logger.info("Pre-loaded %s", settings.ollama_intent_model)
    except ServiceError as e:  # Ollama not running: chat reports it when used
        logger.info("Model pre-load skipped: %s", e.detail)


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


PRIVATE_PATHS = ("/api/cart", "/api/orders", "/api/auth", "/api/assistant", "/api/contact")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    if request.url.path.startswith(PRIVATE_PATHS):
        # carts, orders and account data are per-user: never let a shared cache keep them
        response.headers.setdefault("Cache-Control", "no-store")
    return response


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
