from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/app.db"
    max_upload_size: int = 50 * 1024 * 1024
    default_data_ttl_hours: int = 24
    dataset_storage_path: Path = Path("./data/uploads")
    chart_storage_path: Path = Path("./data/charts")
    frontend_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


settings = Settings()
