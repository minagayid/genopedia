"""Environment-based application settings."""

from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")
    app_name: str = "Genopedia"
    app_env: str = "development"
    database_url: str = "sqlite:///./genopedia.db"
    secure_cookies: bool = False
    cookie_domain: str | None = None
    session_ttl_seconds: int = 604800
    allowed_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if not 300 <= self.session_ttl_seconds <= 2592000:
            raise ValueError("SESSION_TTL_SECONDS must be between 300 and 2592000")
        if self.app_env.lower() == "production":
            if not self.secure_cookies:
                raise ValueError("SECURE_COOKIES=true is required in production")
            if self.database_url.lower().startswith("sqlite:"):
                raise ValueError("Production requires a persistent PostgreSQL DATABASE_URL")
        return self
    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.allowed_origins.split(",") if origin.strip()]

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
