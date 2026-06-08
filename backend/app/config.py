from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/argus"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
