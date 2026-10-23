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

    # Email through Resend (https://resend.com). Empty key = emails are skipped.
    # onboarding@resend.dev only delivers to your own Resend account email; verify a domain to email anyone.
    resend_api_key: str = ""
    email_from: str = "Kad AI <onboarding@resend.dev>"
    site_url: str = "http://localhost:3000"  # link in emails

    # false on hosts without Ollama (e.g. Render free): no model calls, the assistant uses its rules
    # and a plain search, and says the AI runs in the local version.
    ai_enabled: bool = True
    # "ollama" = local models (default); "groq" = hosted models for deployments without Ollama.
    llm_provider: str = "ollama"
    groq_api_key: str = ""  # secret: .env / host settings only
    groq_intent_model: str = "openai/gpt-oss-20b"  # JSON extraction, very fast
    groq_response_model: str = "llama-3.3-70b-versatile"  # customer-facing text
    groq_daily_limit: int = 500  # all visitors together; over it the assistant uses rules only
    # Web search (https://serper.dev) for general produce questions: recipes, storage, season.
    # Never used for prices, stock or nutrition numbers. Empty key = off.
    serper_api_key: str = ""
    search_daily_limit: int = 100  # all visitors together (Serper's free plan is 2,500 searches total)
    search_per_ip_per_hour: int = 5
    ollama_base_url: str = "http://localhost:11434"
    ollama_intent_model: str = "qwen3:4b"
    ollama_response_model: str = "llama3.2"
    # Model for every CrewAI agent (optional Stage 8). One model only: CrewAI talks to Ollama's
    # OpenAI-compatible API, where we cannot unload between agents or turn off qwen's thinking.
    ollama_crew_model: str = "llama3.2"
    ollama_connect_timeout: float = 5.0
    ollama_read_timeout: float = 180.0  # first call includes loading the model from disk
    # How long Ollama keeps a model in RAM after a call ("5m", "30s", "0" = unload immediately).
    ollama_keep_alive: str = "30m"
    # Context window in tokens. Smaller = less RAM for the KV cache; 4096 is plenty for chat turns.
    ollama_num_ctx: int = 4096
    # Load the intent model in the background at startup, so the first chat doesn't pay ~10-40 s.
    ollama_prewarm: bool = True
    # Abuse protection for the one local model. Chat requests waiting for the model beyond this
    # many get 503 "busy" at once instead of piling up; a waiter gives up after queue_wait seconds.
    ollama_max_waiting: int = 3
    ollama_queue_wait: float = 90.0
    # Assistant chat requests allowed per client IP per minute (rules-only replies count too).
    chat_per_minute: int = 10
    # The CrewAI endpoint is slow (minutes on CPU) and easy to abuse; off unless you turn it on.
    crew_enabled: bool = False
    # Header holding the real client IP, set by your deploy edge (e.g. "x-real-ip" on Vercel).
    # Leave empty locally: forwarded headers from the browser are spoofable. See core/ratelimit.py.
    trusted_ip_header: str = ""


settings = Settings()
