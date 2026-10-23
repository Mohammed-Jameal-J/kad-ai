from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.ai.ollama import OllamaClient, get_ollama
from app.core.config import settings
from app.core.ratelimit import RateLimiter, client_ip, enforce
from app.db.session import get_db
from app.schemas.assistant import ChatRequest, ChatResponse
from app.services import assistant

router = APIRouter(prefix="/api/assistant", tags=["assistant"])
Ollama = Annotated[OllamaClient, Depends(get_ollama)]
CHAT_PER_IP = RateLimiter(limit=settings.chat_per_minute, window_seconds=60)


@router.get("/status")
def assistant_status(ollama: Ollama):
    """Is Ollama reachable, and are the configured models installed? Does not load any model."""
    return ollama.status()


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, db: Annotated[Session, Depends(get_db)], ollama: Ollama, request: Request):
    """Shopping assistant. Product data, prices and totals in the response come from the database.

    Cart changes are only proposed (`pending_action`); confirm them with POST /api/cart/items.
    Send previous turns in `history` to keep conversation context (the server stores none).
    """
    enforce(CHAT_PER_IP, client_ip(request))
    return assistant.chat(db, ollama, body)
