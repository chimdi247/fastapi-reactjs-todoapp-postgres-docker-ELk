from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Database ---------------------------------------------------------
    DATABASE_URL: str

    # --- Auth -------------------------------------------------------------
    # Must be a long random string in any shared environment:
    #   python -c "import secrets; print(secrets.token_urlsafe(48))"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # --- HTTP -------------------------------------------------------------
    # Comma separated list of allowed origins, or "*".
    CORS_ORIGINS: str = "*"

    # --- Observability ----------------------------------------------------
    SERVICE_NAME: str = "todo-backend"
    SERVICE_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "INFO"
    # How often the business-KPI gauges (todo counts) are refreshed from the DB.
    TODO_STATS_INTERVAL_SECONDS: int = 15

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("JWT_SECRET")
    @classmethod
    def _jwt_secret_must_be_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
