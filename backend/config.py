from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./syrhousing.db"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:5173","http://localhost:8000"]'
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email / SendGrid
    SENDGRID_API_KEY: str = ""
    SENDER_EMAIL: str = "noreply@syrhousing.com"
    SENDER_NAME: str = "SyrHousing - DJ AI Business Consultant"
    FRONTEND_URL: str = "http://localhost:5173"

    # LLM provider: "anthropic", "openai", or "none" (offline only)
    LLM_PROVIDER: str = "none"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    LLM_MAX_TOKENS: int = 1024

    # Automated Grant Discovery
    DISCOVERY_ENABLED: bool = True
    DISCOVERY_SCHEDULE_CRON: str = "0 2 * * *"  # Daily at 2 AM (cron format: minute hour day month weekday)
    DISCOVERY_SOURCES: str = "rss_feed"  # Comma-separated: rss_feed,grants_gov_api,web_scrape
    DISCOVERY_MIN_CONFIDENCE: float = 0.5
    DUPLICATE_NAME_THRESHOLD: int = 85  # % similarity for name matching
    DUPLICATE_AGENCY_THRESHOLD: int = 70  # % similarity for agency matching

    # Grants.gov API (optional - RSS works without)
    GRANTS_GOV_API_KEY: str = ""
    GRANTS_GOV_API_URL: str = "https://www.grants.gov/grantsws/rest"

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
