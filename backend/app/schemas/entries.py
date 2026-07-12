from datetime import datetime

from pydantic import Field

from app.schemas.common import ORMModel


class EntryCreate(ORMModel):
    race_id: int
    player_id: int
    entry_number: int = Field(ge=1)
    lane_number: int = Field(ge=1)
    lineup_position: int = Field(ge=1)
    status: str = "confirmed"


class EntryRead(ORMModel):
    id: int
    race_id: int
    player_id: int
    entry_number: int
    lane_number: int
    lineup_position: int
    status: str
    created_at: datetime
    updated_at: datetime


class EntryPlayerRead(ORMModel):
    id: int
    name: str
    player_number: int
    grade: str
    region: str
    status: str


class EntryDetailRead(EntryRead):
    player: EntryPlayerRead
