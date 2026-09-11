from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/argus"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    ENVIRONMENT: str = "development"
    API_KEY: str = "change-me-in-production"
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    # Locked-down public demo deployment (see DEMO_DEPLOYMENT.md). When true,
    # the target validator only accepts the bundled juice-shop target, the
    # scan-creation rate limit tightens, and auth requires DEMO_API_KEY
    # instead of API_KEY — everything else is unaffected.
    DEMO_MODE: bool = False
    DEMO_API_KEY: str = "change-me-in-production"
    DEMO_SCAN_DAILY_LIMIT: int = 500

    class Config:
        env_file = ".env"

    @property
    def active_api_key(self) -> str:
        return self.DEMO_API_KEY if self.DEMO_MODE else self.API_KEY

settings = Settings()
