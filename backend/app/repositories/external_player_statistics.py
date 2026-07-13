from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.external_player_statistics import ExternalPlayerStatistic


class ExternalPlayerStatisticRepository:
    def get_by_id(self, db: Session, statistic_id: int) -> ExternalPlayerStatistic | None:
        return db.get(ExternalPlayerStatistic, statistic_id)

    def list_filtered(
        self,
        db: Session,
        *,
        offset: int,
        limit: int,
        year: str | None = None,
        racer_name: str | None = None,
        period_number: str | None = None,
        grade: str | None = None,
    ) -> tuple[list[ExternalPlayerStatistic], int]:
        filters = []
        if year:
            filters.append(ExternalPlayerStatistic.standard_year == year)
        if racer_name:
            filters.append(ExternalPlayerStatistic.racer_name.ilike(f"%{racer_name}%"))
        if period_number:
            filters.append(ExternalPlayerStatistic.period_number == period_number)
        if grade:
            filters.append(ExternalPlayerStatistic.grade == grade)
        total = db.scalar(
            select(func.count()).select_from(ExternalPlayerStatistic).where(*filters)
        ) or 0
        query = (
            select(ExternalPlayerStatistic)
            .where(*filters)
            .order_by(ExternalPlayerStatistic.standard_year.desc(), ExternalPlayerStatistic.id.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(db.scalars(query).all()), int(total)
