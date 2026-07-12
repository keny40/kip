from datetime import date, datetime, time

from pydantic import Field, model_validator

from app.schemas.common import ORMModel
from app.schemas.entries import EntryDetailRead
from app.schemas.results import ResultDetailRead


class RaceCreate(ORMModel):
    race_date: date
    track_id: int | None = None
    track_name: str | None = Field(default=None, min_length=1, max_length=255)
    race_number: int = Field(ge=1)
    scheduled_start_time: time
    status: str = "scheduled"

    @model_validator(mode="after")
    def validate_track_identity(self):
        if self.track_id is None and self.track_name is None:
            raise ValueError("track_id or track_name is required")
        return self


class RaceRead(ORMModel):
    id: int
    race_date: date
    track_id: int
    track_name: str
    race_number: int
    scheduled_start_time: time
    status: str
    created_at: datetime
    updated_at: datetime


class RaceDetailRead(RaceRead):
    entries: list[EntryDetailRead]
    results: list[ResultDetailRead] = Field(default_factory=list)
