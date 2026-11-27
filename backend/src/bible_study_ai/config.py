
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Bible Study AI"
    environment: str = "development"

    database_url: str
    usfm_corpus_path: Path

    chroma_persist_directory: Path = BACKEND_DIR / "data" / "chroma"
    chroma_collection_name: str = "bible_passages"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
