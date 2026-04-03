from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = "changeme"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/macropulse"
    database_url_sync: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/macropulse"

    fred_api_key: str = ""
    cache_ttl_chart: int = 3600


@lru_cache
def get_settings() -> Settings:
    return Settings()
