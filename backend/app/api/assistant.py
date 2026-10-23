from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.ollama import OllamaClient, get_ollama
from app.db.session import get_db
from app.schemas.assistant import ChatRequest, ChatResponse
from app.services import assistant

router = APIRouter(prefix="/api/assistant", tags=["assistant"])
Ollama = Annotated[OllamaClient, Depends(get_ollama)]


@router.get("/status")
def assistant_status(ollama: Ollama):
    """Is Ollama reachable, and are the configured models installed? Does not load any model."""
    return ollama.status()


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, db: Annotated[Session, Depends(get_db)], ollama: Ollama):
    """Shopping assistant. Product data, prices and totals in the response come from the database.

    Cart changes are only proposed (`pending_action`); confirm them with POST /api/cart/items.
    Send previous turns in `history` to keep conversation context (the server stores none).
    """
    return assistant.chat(db, ollama, body)
