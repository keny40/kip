from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.external_players import ExternalPlayer


class ExternalPlayerRepository:
    def get_by_id(self, db: Session, external_player_id: int) -> ExternalPlayer | None:
        return db.get(ExternalPlayer, external_player_id)

    def get_by_source_external_id(
        self,
        db: Session,
        *,
        source: str,
        external_id: str,
    ) -> ExternalPlayer | None:
        query = select(ExternalPlayer).where(
            ExternalPlayer.source == source,
            ExternalPlayer.external_id == external_id,
        )
        return db.scalars(query).first()

    def list_filtered(
        self,
        db: Session,
        *,
        offset: int,
        limit: int,
        source: str | None = None,
        name: str | None = None,
        period_number: str | None = None,
        grade: str | None = None,
        status: str | None = None,
    ) -> tuple[list[ExternalPlayer], int]:
        filters = []
        if source:
            filters.append(ExternalPlayer.source == source)
        if name:
            filters.append(ExternalPlayer.name.ilike(f"%{name}%"))
        if period_number:
            filters.append(ExternalPlayer.period_number == period_number)
        if grade:
            filters.append(ExternalPlayer.grade == grade)
        if status:
            filters.append(ExternalPlayer.status == status)

        total = db.scalar(select(func.count()).select_from(ExternalPlayer).where(*filters)) or 0
        query = (
            select(ExternalPlayer)
            .where(*filters)
            .order_by(ExternalPlayer.source.asc(), ExternalPlayer.external_id.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(db.scalars(query).all()), int(total)
