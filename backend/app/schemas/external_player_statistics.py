from datetime import datetime
from decimal import Decimal

from app.schemas.common import ORMModel


class ExternalPlayerStatisticRead(ORMModel):
    id: int
    source: str
    standard_year: str
    racer_name: str
    period_number: str | None
    grade: str
    run_count: int | None
    run_day_count: int | None
    rank1_count: int | None
    rank2_count: int | None
    rank3_count: int | None
    rank4_count: int | None
    rank5_count: int | None
    rank6_count: int | None
    rank7_count: int | None
    rank8_count: int | None
    rank9_count: int | None
    eliminated_count: int | None
    win_rate: Decimal | None
    high_rate: Decimal | None
    high_3_rate: Decimal | None
    collected_at: datetime
    created_at: datetime
    updated_at: datetime


class PlayerMatchCandidateRead(ORMModel):
    statistic_id: int
    standard_year: str
    masked_racer_name: str
    period_number: str | None
    statistic_grade: str
    candidate_count: int
    match_status: str
    masked_external_id: str | None
    external_grade: str | None
    grade_matches: bool | None
