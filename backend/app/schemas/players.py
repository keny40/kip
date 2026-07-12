from datetime import datetime

from pydantic import Field

from app.schemas.common import ORMModel


class PlayerCreate(ORMModel):
    name: str = Field(min_length=1, max_length=255)
    player_number: int = Field(ge=1)
    grade: str = Field(min_length=1, max_length=20)
    region: str = Field(min_length=1, max_length=100)
    status: str = "active"


class PlayerRead(ORMModel):
    id: int
    name: str
    player_number: int
    grade: str
    region: str
    status: str
    created_at: datetime
    updated_at: datetime
