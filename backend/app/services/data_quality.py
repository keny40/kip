from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.external_player_statistics import ExternalPlayerStatistic
from app.models.external_players import ExternalPlayer
from app.models.players import Player
from app.services.player_match_candidates import MATCH_STATUSES, PlayerMatchCandidateService


def _missing(value: str | None) -> bool:
    return value is None or not value.strip()


def _unknown(value: str | None) -> bool:
    return _missing(value) or value.strip().lower() == "unknown"


class DataQualitySummaryService:
    def build(self, db: Session, *, year: str | None = None, source: str | None = None) -> dict:
        external_query = select(ExternalPlayer)
        if source:
            external_query = external_query.where(ExternalPlayer.source == source)
        external_players = list(db.scalars(external_query).all())

        statistic_query = select(ExternalPlayerStatistic)
        if year:
            statistic_query = statistic_query.where(ExternalPlayerStatistic.standard_year == year)
        if source:
            statistic_query = statistic_query.where(ExternalPlayerStatistic.source == source)
        statistics = list(db.scalars(statistic_query).all())

        reports = PlayerMatchCandidateService().build_report(
            db, year=year, source=source, limit=max(1, len(statistics))
        ) if statistics else []
        statuses = Counter(item.match_status for item in reports)
        status_counts = {status: statuses.get(status, 0) for status in MATCH_STATUSES}
        total = len(statistics)
        unique = status_counts["UNIQUE_CANDIDATE"]

        return {
            "counts": {
                "players_count": db.scalar(select(func.count()).select_from(Player)) or 0,
                "external_players_count": len(external_players),
                "external_player_statistics_count": total,
            },
            "external_players_quality": {
                "missing_name_count": sum(_missing(item.name) for item in external_players),
                "missing_period_number_count": sum(_missing(item.period_number) for item in external_players),
                "unknown_grade_count": sum(_unknown(item.grade) for item in external_players),
                "unknown_region_count": sum(_unknown(item.region) for item in external_players),
                "unknown_status_count": sum(_unknown(item.status) for item in external_players),
                "duplicate_source_external_id_count": self._duplicate_count(
                    db, ExternalPlayer, (ExternalPlayer.source, ExternalPlayer.external_id),
                    source=source,
                ),
                "latest_collected_at": max((item.collected_at for item in external_players), default=None),
            },
            "statistics_quality": {
                "missing_name_count": sum(_missing(item.racer_name) for item in statistics),
                "missing_period_number_count": sum(_missing(item.period_number) for item in statistics),
                "unknown_grade_count": sum(_unknown(item.grade) for item in statistics),
                "provisional_duplicate_count": self._statistic_duplicate_count(db, year, source),
                "invalid_or_null_run_count": sum(item.run_count is None or item.run_count < 0 for item in statistics),
                "null_win_rate_count": sum(item.win_rate is None for item in statistics),
                "null_high_rate_count": sum(item.high_rate is None for item in statistics),
                "null_high_3_rate_count": sum(item.high_3_rate is None for item in statistics),
                "latest_collected_at": max((item.collected_at for item in statistics), default=None),
            },
            "match_status_counts": status_counts,
            "coverage": {
                "total_statistics": total,
                "unique_candidate_count": unique,
                "unmatched_count": status_counts["NO_CANDIDATE"] + status_counts["MISSING_PERIOD_NUMBER"] + status_counts["GRADE_MISMATCH"],
                "multiple_candidate_count": status_counts["MULTIPLE_CANDIDATES"],
                "unique_candidate_rate": round(unique * 100 / total, 1) if total else 0.0,
            },
        }

    def _duplicate_count(self, db, model, columns, *, source=None) -> int:
        query = select(func.count().label("row_count")).select_from(model)
        if source:
            query = query.where(model.source == source)
        groups = db.execute(query.group_by(*columns).having(func.count() > 1)).scalars().all()
        return sum(count - 1 for count in groups)

    def _statistic_duplicate_count(self, db: Session, year: str | None, source: str | None) -> int:
        query = select(func.count().label("row_count")).select_from(ExternalPlayerStatistic)
        if year:
            query = query.where(ExternalPlayerStatistic.standard_year == year)
        if source:
            query = query.where(ExternalPlayerStatistic.source == source)
        groups = db.execute(query.group_by(
            ExternalPlayerStatistic.source,
            ExternalPlayerStatistic.standard_year,
            ExternalPlayerStatistic.racer_name,
            ExternalPlayerStatistic.period_number,
        ).having(func.count() > 1)).scalars().all()
        return sum(count - 1 for count in groups)
