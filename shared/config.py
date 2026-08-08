from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Intern AI Agents Lab"
    VERSION: str = "1.0.0"

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

    MISTRAL_API_KEY: str = ""

    # Development only: when true, get_current_user returns a dev user and skips
    # Supabase token validation. Never enable this in a deployed environment.
    DISABLE_AUTH: bool = False

    SUPABASE_URL: str = ""
    SUPABASE_PUBLISHABLE_KEY: str = ""
    SUPABASE_AUTH_TIMEOUT_SECONDS: float = 5.0

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def supabase_auth_url(self) -> str:
        return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1/user"

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.supabase.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()