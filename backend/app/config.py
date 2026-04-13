"""
LogSentinel — Application Configuration
Loads all settings from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Central configuration loaded from environment variables."""

    # ── Database ──
    DATABASE_URL: str = "postgresql+asyncpg://logsentinel:changeme@postgres:5432/logsentinel"
    POSTGRES_USER: str = "logsentinel"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "logsentinel"

    # ── Redis ──
    REDIS_URL: str = "redis://redis:6379/0"

    # ── LLM ──
    LLM_PROVIDER: str = Field(default="gemini", description="gemini or groq")
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # ── Threat Intelligence ──
    ABUSEIPDB_API_KEY: Optional[str] = None
    ABUSEIPDB_ENABLED: bool = True

    # ── Auth ──
    AUTH_SECRET: str = ""
    ALLOWED_EMAILS: str = ""
    NEXTAUTH_URL: str = "http://localhost:3000"

    # ── Limits ──
    MAX_FILE_SIZE_MB: int = 10
    MAX_LOG_LINES: int = 50000
    SAMPLING_THRESHOLD: int = 10000

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def allowed_emails_set(self) -> set[str]:
        if not self.ALLOWED_EMAILS:
            return set()
        return {e.strip().lower() for e in self.ALLOWED_EMAILS.split(",") if e.strip()}

    @property
    def sync_database_url(self) -> str:
        """Synchronous DB URL for Alembic & Celery."""
        if "sqlite+aiosqlite" in self.DATABASE_URL:
            return self.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
