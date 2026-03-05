import os
from pathlib import Path

from pydantic import AnyUrl, Field, ValidationError, BaseSettings


class Settings(BaseSettings):
    environment: str = Field("development", env="ENVIRONMENT")
    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")
    database_url: AnyUrl = Field(..., env="DATABASE_URL")

    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = "utf-8"


def load_settings() -> Settings:
    try:
        settings = Settings()
    except ValidationError as exc:
        missing = [err["loc"][0] for err in exc.errors()]
        raise RuntimeError(
            f"Missing or invalid environment variables: {', '.join(missing)}"
        ) from exc
    return settings


CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.py"

try:
    SETTINGS = load_settings()
except Exception as e:
    raise SystemExit(f"Failed to initialize configuration: {e}") from e

DATABASE_URL = SETTINGS.database_url
APP_HOST = SETTINGS.app_host
APP_PORT = SETTINGS.app_port
ENVIRONMENT = SETTINGS.environment