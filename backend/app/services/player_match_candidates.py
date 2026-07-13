from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.external_player_statistics import ExternalPlayerStatistic
from app.models.external_players import ExternalPlayer


MATCH_STATUSES = {
    "UNIQUE_CANDIDATE",
    "NO_CANDIDATE",
    "MULTIPLE_CANDIDATES",
    "MISSING_PERIOD_NUMBER",
    "GRADE_MISMATCH",
}


@dataclass(frozen=True)
class PlayerMatchCandidate:
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


class PlayerMatchCandidateService:
    def build_report(
        self,
        db: Session,
        *,
        year: str | None = None,
        racer_name: str | None = None,
        period_number: str | None = None,
        grade: str | None = None,
        limit: int = 100,
        match_status: str | None = None,
    ) -> list[PlayerMatchCandidate]:
        if match_status and match_status not in MATCH_STATUSES:
            raise ValueError("Unsupported match_status")
        query = select(ExternalPlayerStatistic).order_by(ExternalPlayerStatistic.id.asc())
        if year:
            query = query.where(ExternalPlayerStatistic.standard_year == year)
        if racer_name:
            query = query.where(ExternalPlayerStatistic.racer_name.ilike(f"%{racer_name}%"))
        if period_number:
            query = query.where(ExternalPlayerStatistic.period_number == period_number)
        if grade:
            query = query.where(ExternalPlayerStatistic.grade == grade)
        statistics = list(db.scalars(query.limit(limit)).all())
        results = [self._match_one(db, statistic) for statistic in statistics]
        if match_status:
            results = [item for item in results if item.match_status == match_status]
        return results

    def _match_one(
        self,
        db: Session,
        statistic: ExternalPlayerStatistic,
    ) -> PlayerMatchCandidate:
        if not statistic.period_number:
            return self._result(statistic, [], "MISSING_PERIOD_NUMBER")

        query = select(ExternalPlayer).where(
            ExternalPlayer.name == statistic.racer_name,
            ExternalPlayer.period_number == statistic.period_number,
        )
        candidates = list(db.scalars(query).all())
        if not candidates:
            return self._result(statistic, candidates, "NO_CANDIDATE")
        if len(candidates) > 1:
            return self._result(statistic, candidates, "MULTIPLE_CANDIDATES")
        if candidates[0].grade != statistic.grade:
            return self._result(statistic, candidates, "GRADE_MISMATCH")
        return self._result(statistic, candidates, "UNIQUE_CANDIDATE")

    def _result(
        self,
        statistic: ExternalPlayerStatistic,
        candidates: list[ExternalPlayer],
        status: str,
    ) -> PlayerMatchCandidate:
        candidate = candidates[0] if len(candidates) == 1 else None
        return PlayerMatchCandidate(
            statistic_id=statistic.id,
            standard_year=statistic.standard_year,
            masked_racer_name=_mask_name(statistic.racer_name),
            period_number=statistic.period_number,
            statistic_grade=statistic.grade,
            candidate_count=len(candidates),
            match_status=status,
            masked_external_id=_mask_external_id(candidate.external_id) if candidate else None,
            external_grade=candidate.grade if candidate else None,
            grade_matches=(candidate.grade == statistic.grade) if candidate else None,
        )


def _mask_name(value: str) -> str:
    return "*" if len(value) <= 1 else value[0] + "*" * (len(value) - 1)


def _mask_external_id(value: str) -> str:
    return value[:4] + "*" * max(0, len(value) - 4)
