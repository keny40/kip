from datetime import datetime

from pydantic import Field

from app.schemas.common import ORMModel


class TrackCreate(ORMModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    region: str = Field(min_length=1, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    status: str = "active"


class TrackUpdate(ORMModel):
    code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    region: str | None = Field(default=None, min_length=1, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    status: str | None = None


class TrackRead(ORMModel):
    id: int
    code: str
    name: str
    region: str
    address: str | None
    status: str
    created_at: datetime
    updated_at: datetime
