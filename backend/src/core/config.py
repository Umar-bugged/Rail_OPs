from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Railway Delay Operations"
    environment: str = "development"
    api_prefix: str = "/api"

    data_dir: Path = PROJECT_ROOT / "data" / "raw"
    fallback_data_dir: Path = PROJECT_ROOT.parent
    processed_data_dir: Path = PROJECT_ROOT / "data" / "processed"
    model_dir: Path = PROJECT_ROOT / "models"

    delay_chunk_size: int = 150_000
    max_training_rows: int = 500_000
    max_analytics_rows: int = 200_000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,https://rail-dktjzljgb-hustl-3-r-s-projects.vercel.app,https://rail-ops-henna.vercel.app"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
    settings.model_dir.mkdir(parents=True, exist_ok=True)
    return settings
