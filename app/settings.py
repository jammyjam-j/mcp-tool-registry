import os
from pathlib import Path

from pydantic import AnyHttpUrl, BaseSettings, Field, PostgresDsn, validator


class DatabaseConfig(BaseSettings):
    url: PostgresDsn = Field(..., env="DATABASE_URL")
    pool_size: int = Field(20, env="DB_POOL_SIZE")
    max_overflow: int = Field(10, env="DB_MAX_OVERFLOW")

    @validator("pool_size", "max_overflow")
    def validate_positive(cls, v):
        if v < 0:
            raise ValueError("must be non-negative")
        return v


class AppConfig(BaseSettings):
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    host: str = Field("127.0.0.1", env="HOST")
    port: int = Field(8000, env="PORT")

    @validator("port")
    def validate_port(cls, v):
        if not (1024 <= v <= 65535):
            raise ValueError("port must be between 1024 and 65535")
        return v


class ToolRegistrySettings(BaseSettings):
    discovery_interval: int = Field(60, env="DISCOVERY_INTERVAL_SECONDS")
    max_workers: int = Field(10, env="MAX_WORKERS")

    @validator("discovery_interval", "max_workers")
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError("must be positive")
        return v


class Settings(BaseSettings):
    database: DatabaseConfig
    app: AppConfig
    registry: ToolRegistrySettings

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_settings() -> Settings:
    return Settings(
        database=DatabaseConfig(),
        app=AppConfig(),
        registry=ToolRegistrySettings()
    )


SETTINGS = load_settings()
if __name__ == "__main__":
    print(SETTINGS.json(indent=2))