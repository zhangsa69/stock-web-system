from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # 应用
    app_env: str = "development"
    app_debug: bool = True
    app_port: int = 8000
    secret_key: str = "dev-secret-key-change-in-production"
    frontend_url: str = "http://localhost:5173"

    # 数据库
    postgres_db: str = "stock_analysis"
    postgres_user: str = "stock_user"
    postgres_password: str = "change_me_please"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Hermes Agent
    hermes_bin: str = "hermes"
    hermes_home: str = os.path.expanduser("~/.hermes")
    hermes_timeout: int = 600
    hermes_max_workers: int = 4
    hermes_mock: bool = True  # True=本地Mock模式，生产环境设False

    # 任务缓存（天）
    analysis_cache_days: int = 7

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:80,http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
