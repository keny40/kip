from datetime import date
from typing import Any

from pydantic import BaseModel


class RacePredictionRead(BaseModel):
    race_id: int
    race_date: date
    track_code: str | None
    race_number: int
    model_status: str
    reason: str | None
    readiness: dict[str, Any]
    predictions: list[dict[str, Any]]
