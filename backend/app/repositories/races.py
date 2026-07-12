from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.entries import Entry
from app.models.results import Result
from app.models.races import Race
from app.models.tracks import Track


class RaceRepository:
    def list_races(
        self,
        db: Session,
        *,
        race_date: date | None,
        track_name: str | None,
        status: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Race], int]:
        filters = []
        if race_date is not None:
            filters.append(Race.race_date == race_date)
        if track_name:
            filters.append(Track.name == track_name)
        if status:
            filters.append(Race.status == status)

        count_query = select(func.count()).select_from(Race).join(Race.track)
        data_query = select(Race).join(Race.track).options(
            joinedload(Race.entries).joinedload(Entry.player),
            joinedload(Race.track),
        )
        if filters:
            count_query = count_query.where(*filters)
            data_query = data_query.where(*filters)
        total = int(db.scalar(count_query) or 0)
        items = list(
            db.scalars(
                data_query.order_by(Race.race_date.desc(), Race.scheduled_start_time.desc(), Race.race_number.asc())
                .offset(offset)
                .limit(limit)
            ).unique().all()
        )
        return items, total

    def get_by_id(self, db: Session, race_id: int) -> Race | None:
        query = select(Race).where(Race.id == race_id).options(
            joinedload(Race.entries).joinedload(Entry.player),
            joinedload(Race.results).joinedload(Result.player),
            joinedload(Race.track),
        )
        return db.scalars(query).unique().first()

    def get_duplicate(self, db: Session, race_date: date, track_id: int, race_number: int) -> Race | None:
        query = select(Race).where(
            Race.race_date == race_date,
            Race.track_id == track_id,
            Race.race_number == race_number,
        )
        return db.scalars(query).first()

    def create(self, db: Session, race: Race) -> Race:
        db.add(race)
        db.flush()
        db.refresh(race)
        return race
