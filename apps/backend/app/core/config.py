from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "marketmage-backend"
    frankfurter_base_url: str = "https://api.frankfurter.app"
    cache_ttl_seconds: int = 3600
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    database_url: str = "sqlite+pysqlite:///:memory:"
    cors_origins: str = "http://localhost:3000"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
