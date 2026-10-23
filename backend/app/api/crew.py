from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.ai.ollama import OllamaClient, get_ollama
from app.core.config import settings
from app.core.errors import ServiceError
from app.schemas.assistant import ChatResponse

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


class CrewUnavailable(ServiceError):
    status_code = 501


class CrewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., min_length=1, max_length=500)
    budget_inr: int | None = Field(None, ge=1, le=100_000)


@router.post("/crew", response_model=ChatResponse)
def crew_chat(body: CrewRequest, ollama: Annotated[OllamaClient, Depends(get_ollama)]):
    """Optional CrewAI workflow (3 agents + deterministic validation). Much slower than /chat;
    meant for requests that combine a budget with nutrition or planning goals. Needs `crewai` installed."""
    if not settings.crew_enabled:
        raise CrewUnavailable("The CrewAI workflow is turned off. Set CREW_ENABLED=true in .env to use it.")
    try:
        from app.crew.workflow import run_crew  # imported lazily: CrewAI is an optional dependency
    except ImportError:
        raise CrewUnavailable(
            "CrewAI is not installed in this Python environment. Start the backend with "
            "backend\\.venv-crewai (see docs/crewai.md) to use this endpoint."
        )
    return run_crew(body.message, body.budget_inr, ollama)
