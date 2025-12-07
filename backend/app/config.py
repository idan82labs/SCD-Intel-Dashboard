"""Application configuration and settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "CI Research Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # URLs
    FRONTEND_URL: str = "http://localhost:3000"

    # Required API Keys
    ANTHROPIC_API_KEY: str = ""

    # Web Search API Keys (at least one recommended)
    TAVILY_API_KEY: Optional[str] = None
    EXA_API_KEY: Optional[str] = None

    # Optional API Keys
    SAM_GOV_API_KEY: Optional[str] = None
    EPO_CONSUMER_KEY: Optional[str] = None
    EPO_CONSUMER_SECRET: Optional[str] = None
    UN_COMTRADE_KEY: Optional[str] = None

    # SEC EDGAR (no API key required, but needs contact email)
    SEC_EDGAR_CONTACT_EMAIL: str = "research@example.com"

    # Database
    DATABASE_URL: str = "sqlite:///./data/research.db"

    # Redis (optional)
    REDIS_URL: Optional[str] = None

    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100

    # AI Model settings
    DEFAULT_MODEL: str = "claude-sonnet-4-20250514"
    MAX_TOKENS_CHAT: int = 1000
    MAX_TOKENS_PLAN: int = 2000
    MAX_TOKENS_SYNTHESIS: int = 4000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
