from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Intern AI Agents Lab"
    VERSION: str = "1.0.0"
    # Production must be explicit: it must not inherit permissive local defaults.
    ENVIRONMENT: Literal["development", "test", "staging", "production"] = "development"

    DATABASE_URL: str = "sqlite+aiosqlite:///./multiagent.db"
    CREATE_SCHEMA_ON_STARTUP: bool = False

    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "adminpassword"
    POSTGRES_DB: str = "lab_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Event Bus: "redis" (default), "kafka", or "memory"
    EVENT_BUS_TYPE: str = "redis"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    # Transactional outbox: durable event delivery retries. These defaults keep
    # local development responsive while bounding pressure on a failed broker.
    OUTBOX_POLL_SECONDS: float = 1.0
    OUTBOX_BATCH_SIZE: int = 20
    OUTBOX_MAX_ATTEMPTS: int = 10
    OUTBOX_RETRY_SECONDS: float = 2.0
    OUTBOX_CLAIM_SECONDS: int = 30

    # Scientific-watch scheduler. One API process runs this loop; deployments
    # with replicas should enable it on a single worker or invoke /trigger from
    # their external scheduler.
    VEILLE_SCHEDULER_ENABLED: bool = True
    VEILLE_COLLECTION_INTERVAL_HOURS: int = 24

    MISTRAL_API_KEY: str = ""

    # Development only: when true, get_current_user returns a dev user and skips
    # Supabase token validation. Never enable this in a deployed environment.
    DISABLE_AUTH: bool = False

    SUPABASE_URL: str = ""
    SUPABASE_PUBLISHABLE_KEY: str = ""
    SUPABASE_AUTH_TIMEOUT_SECONDS: float = 5.0
    # Comma-separated browser origins allowed to call the API. This is a
    # browser boundary, not authentication; keep it exact in deployed envs.
    CORS_ALLOWED_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5174,http://127.0.0.1:5174"
    )
    # Per-device gateway keys are HMAC-hashed before storage. This is separate
    # from Supabase user authentication; never use a Supabase secret key here.
    GATEWAY_TOKEN_PEPPER: str = "development-only-change-me"
    SENSOR_STALE_AFTER_HOURS: int = 48
    # Production always starts strictly; this offers the same safety in staging.
    STRICT_AGENT_STARTUP: bool = False

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def supabase_auth_url(self) -> str:
        return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1/user"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode="after")
    def reject_unsafe_production_configuration(self) -> "Settings":
        if not self.is_production:
            return self

        errors: list[str] = []
        if self.DISABLE_AUTH:
            errors.append("DISABLE_AUTH must be false")
        if self.CREATE_SCHEMA_ON_STARTUP:
            errors.append("CREATE_SCHEMA_ON_STARTUP must be false; run Alembic before startup")
        if self.database_url.startswith("sqlite"):
            errors.append("DATABASE_URL must use PostgreSQL, not SQLite")
        if self.EVENT_BUS_TYPE.lower() == "memory":
            errors.append("EVENT_BUS_TYPE must be redis or kafka, not memory")
        if self.VEILLE_COLLECTION_INTERVAL_HOURS < 1:
            errors.append("VEILLE_COLLECTION_INTERVAL_HOURS must be at least 1")
        if not self.SUPABASE_URL or not self.SUPABASE_PUBLISHABLE_KEY:
            errors.append("SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY must be configured")
        if not self.cors_allowed_origins:
            errors.append("CORS_ALLOWED_ORIGINS must list the deployed frontend origin")
        elif any(origin == "*" for origin in self.cors_allowed_origins):
            errors.append("CORS_ALLOWED_ORIGINS must not use wildcard * in production")
        if not self.GATEWAY_TOKEN_PEPPER or self.GATEWAY_TOKEN_PEPPER == "development-only-change-me":
            errors.append("GATEWAY_TOKEN_PEPPER must be a private production secret")
        if errors:
            raise ValueError("Unsafe production configuration: " + "; ".join(errors))
        return self

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.supabase.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
