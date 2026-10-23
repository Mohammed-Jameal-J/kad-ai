from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent

PRICE_NOTE = "Demonstration prices only. These are not live market prices."


class Settings(BaseSettings):
    """Values come from environment variables or the project-root .env file."""

    model_config = SettingsConfigDict(env_file=PROJECT_DIR / ".env", extra="ignore")

    app_name: str = "Kad AI"
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'kadai.db').as_posix()}"
    # JSON list in .env, e.g. CORS_ORIGINS=["http://localhost:3000"]
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    max_request_bytes: int = 64 * 1024
    # Session cookie only over HTTPS. Keep false for http://localhost; set true when deployed.
    cookie_secure: bool = False

    ollama_base_url: str = "http://localhost:11434"
    ollama_intent_model: str = "qwen3:4b"
    ollama_response_model: str = "llama3.2"
    # Model for every CrewAI agent (optional Stage 8). One model only: CrewAI talks to Ollama's
    # OpenAI-compatible API, where we cannot unload between agents or turn off qwen's thinking.
    ollama_crew_model: str = "llama3.2"
    ollama_connect_timeout: float = 5.0
    ollama_read_timeout: float = 180.0  # first call includes loading the model from disk
    # How long Ollama keeps a model in RAM after a call ("5m", "30s", "0" = unload immediately).
    ollama_keep_alive: str = "5m"
    # Context window in tokens. Smaller = less RAM for the KV cache; 4096 is plenty for chat turns.
    ollama_num_ctx: int = 4096


settings = Settings()
