import datetime
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Объявление переменных окружения
    """

    # PostgreSQL async URL, например: postgresql+asyncpg://user:pass@localhost:5432/db
    SQLALCHEMY_URL: str
    SQLALCHEMY_TEST_URL: str = "sqlite+aiosqlite:///testdb.sqlite3"

    # ChromaDB
    CHROMA_HOST: Optional[str] = None
    CHROMA_PORT: Optional[int] = None
    CHROMA_SSL: bool = False
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    CHROMA_COLLECTION: str = "memories"

    # ChromaDB Cloud
    CHROMA_API_KEY: Optional[str] = None
    CHROMA_TENANT: Optional[str] = None
    CHROMA_DB_NAME: Optional[str] = None

    # Симуляция
    SIMULATION_TICK_SECONDS: float = 1.0
    SIMULATION_DEFAULT_SPEED: float = 1.0

    # LLM (OpenAI совместимый)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Общие настройки
    API_TITLE: str = "КИБЕР РЫВОК API"
    API_VERSION: str = "0.1.0"

    model_config = SettingsConfigDict(
        # Ищем .env в каталоге backend (рядом с проектом)
        env_file=str(Path(__file__).resolve().parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings: Settings = Settings()
