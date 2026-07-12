from datetime import date, datetime

from app.schemas.common import ORMModel


class TrackSummaryRead(ORMModel):
    track_id: int
    track_name: str
    code: str
    region: str
    total_races: int
    completed_races: int
    total_entries: int
    unique_players: int
    latest_race_date: date | None
    race_status_counts: dict[str, int]
    grade_counts: dict[str, int]
    recent_30_races: list[dict[str, object]]


class TrackPlayerStatRead(ORMModel):
    player_id: int
    player_number: int
    name: str
    grade: str
    starts: int
    wins: int
    top2: int
    top3: int
    win_rate: float
    top2_rate: float
    top3_rate: float
    disqualified_count: int
    withdrawn_count: int


class RaceSummaryRead(ORMModel):
    total_races: int
    scheduled_races: int
    in_progress_races: int
    completed_races: int
    total_players: int
    total_results: int
    latest_race_date: date | None
    track_count: int
