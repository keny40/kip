from datetime import datetime, date, time

from pydantic import Field

from app.schemas.common import ORMModel
from app.schemas.players import PlayerRead


class ResultCreate(ORMModel):
    race_id: int
    player_id: int
    finish_position: int = Field(ge=1)
    finish_time: str | None = Field(default=None, max_length=50)
    result_status: str = "finished"
    points: int | None = Field(default=None, ge=0)


class ResultUpdate(ORMModel):
    finish_position: int | None = Field(default=None, ge=1)
    finish_time: str | None = Field(default=None, max_length=50)
    result_status: str | None = None
    points: int | None = Field(default=None, ge=0)


class ResultRead(ORMModel):
    id: int
    race_id: int
    player_id: int
    finish_position: int
    finish_time: str | None
    result_status: str
    points: int | None
    created_at: datetime
    updated_at: datetime


class ResultPlayerRead(ORMModel):
    id: int
    name: str
    player_number: int
    grade: str
    region: str
    status: str


class ResultRaceRead(ORMModel):
    id: int
    race_date: date
    track_name: str
    race_number: int
    scheduled_start_time: time
    status: str


class ResultDetailRead(ResultRead):
    player: ResultPlayerRead
    race: ResultRaceRead


class RaceResultsRead(ORMModel):
    race_id: int
    race_date: date
    track_name: str
    race_number: int
    scheduled_start_time: time
    status: str
    results: list[ResultDetailRead]


class ResultListItemRead(ORMModel):
    id: int
    race_id: int
    player_id: int
    race_date: date
    track_name: str
    result_status: str
    finish_position: int
    points: int | None


class ResultStatisticsRead(ORMModel):
    total_races: int
    finished_count: int
    first_place_count: int
    second_place_count: int
    third_place_count: int
    win_rate: float
    place_rate: float
    dnf_count: int
    current_streak: int
    recent_five_results: list[ResultDetailRead]


class PlayerStatisticsFiltersRead(ORMModel):
    track_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    last_n: int | None = None
    grade: str | None = None


class PlayerStatisticsResponseRead(ORMModel):
    filters: PlayerStatisticsFiltersRead
    statistics: ResultStatisticsRead


class RaceHistoryItemRead(ORMModel):
    race_id: int
    race_date: date
    track_name: str
    race_number: int
    scheduled_start_time: time
    result_status: str
    finish_position: int | None
    finish_time: str | None
    points: int | None


class RaceHistoryRead(ORMModel):
    player_id: int
    player_name: str
    player_number: int
    grade: str
    region: str
    history: list[RaceHistoryItemRead]
