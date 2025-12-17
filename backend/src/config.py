"""アプリケーション設定"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリケーション設定"""

    # Database
    database_url: str = "postgresql://trader:localdev@localhost:5432/trading"

    # App
    debug: bool = True
    log_level: str = "INFO"
    api_prefix: str = "/api"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    return Settings()
