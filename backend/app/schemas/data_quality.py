from datetime import datetime

from pydantic import BaseModel


class DataQualityCounts(BaseModel):
    players_count: int
    external_players_count: int
    external_player_statistics_count: int


class ExternalPlayersQuality(BaseModel):
    missing_name_count: int
    missing_period_number_count: int
    unknown_grade_count: int
    unknown_region_count: int
    unknown_status_count: int
    duplicate_source_external_id_count: int
    latest_collected_at: datetime | None


class StatisticsQuality(BaseModel):
    missing_name_count: int
    missing_period_number_count: int
    unknown_grade_count: int
    provisional_duplicate_count: int
    invalid_or_null_run_count: int
    null_win_rate_count: int
    null_high_rate_count: int
    null_high_3_rate_count: int
    latest_collected_at: datetime | None


class MatchStatusCounts(BaseModel):
    UNIQUE_CANDIDATE: int
    NO_CANDIDATE: int
    MULTIPLE_CANDIDATES: int
    MISSING_PERIOD_NUMBER: int
    GRADE_MISMATCH: int


class MatchCoverage(BaseModel):
    total_statistics: int
    unique_candidate_count: int
    unmatched_count: int
    multiple_candidate_count: int
    unique_candidate_rate: float


class DataQualitySummaryRead(BaseModel):
    counts: DataQualityCounts
    external_players_quality: ExternalPlayersQuality
    statistics_quality: StatisticsQuality
    match_status_counts: MatchStatusCounts
    coverage: MatchCoverage
