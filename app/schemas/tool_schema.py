from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field, root_validator, validator


class ToolBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    version: str = Field(..., regex=r"^\d+\.\d+\.\d+$")
    config: Optional[Dict[str, str]] = None


class ToolCreate(ToolBase):
    @validator("config", pre=True, always=True)
    def validate_config(cls, v):
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("config must be a dictionary")
        for key, value in v.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("config keys and values must be strings")
        return v


class ToolUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    version: Optional[str] = Field(None, regex=r"^\d+\.\d+\.\d+$")
    config: Optional[Dict[str, str]] = None

    @validator("config", pre=True, always=True)
    def validate_config(cls, v):
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("config must be a dictionary")
        for key, value in v.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("config keys and values must be strings")
        return v

    @root_validator
    def check_at_least_one_field(cls, values):
        if not any(values.values()):
            raise ValueError("At least one field must be provided for update")
        return values


class ToolRead(ToolBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

    @validator("id", pre=True, always=True)
    def validate_uuid(cls, v):
        try:
            import uuid
            uuid.UUID(str(v))
        except Exception:
            raise ValueError("id must be a valid UUID")
        return str(v)