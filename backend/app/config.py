"""Application settings from environment (no secrets in code)."""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Security
    SECRET_KEY: str = Field(
        default="",
        description="JWT signing key; required in production (set APP_ENV=production).",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    APP_ENV: str = Field(default="development", description="development | staging | production")

    # HTTP / CORS (comma-separated origins, e.g. http://localhost:5173,https://app.example.com)
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Allowed browser origins for CORS.",
    )

    # Paths
    ML_MODELS_PATH: str = Field(default="models/", description="Directory for joblib ML artifacts.")
    AUDIT_LOG_PATH: str = Field(default="audit.log", description="Path for audit log file.")

    @model_validator(mode="after")
    def production_requires_secret(self) -> "Settings":
        if self.APP_ENV == "production" and (not self.SECRET_KEY or len(self.SECRET_KEY) < 32):
            raise ValueError(
                "SECRET_KEY must be set and at least 32 characters when APP_ENV=production"
            )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_secret_key() -> str:
    """JWT secret: env in all real deployments; dev-only default when not production."""
    s = get_settings()
    if s.SECRET_KEY:
        return s.SECRET_KEY
    if s.APP_ENV == "production":
        raise RuntimeError("SECRET_KEY is required when APP_ENV=production")
    # Development default — must never be used in production (guarded above).
    return "dev-only-insecure-jwt-key-change-me"
