from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.races import Race
from app.models.results import Result
from app.models.tracks import Track


class ResultRepository:
    def list_results(
        self,
        db: Session,
        *,
        race_id: int | None,
        player_id: int | None,
        race_date: date | None,
        track_name: str | None,
        result_status: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Result], int]:
        filters = []
        if race_id is not None:
            filters.append(Result.race_id == race_id)
        if player_id is not None:
            filters.append(Result.player_id == player_id)
        if result_status:
            filters.append(Result.result_status == result_status)

        data_query = select(Result).join(Result.race).join(Race.track).options(
            joinedload(Result.player),
            joinedload(Result.race).joinedload(Race.track),
        )
        count_query = select(func.count()).select_from(Result).join(Result.race).join(Race.track)

        if filters:
            data_query = data_query.where(*filters)
            count_query = count_query.where(*filters)

        if race_date is not None:
            data_query = data_query.where(Race.race_date == race_date)
            count_query = count_query.where(Race.race_date == race_date)
        if track_name:
            data_query = data_query.where(Track.name == track_name)
            count_query = count_query.where(Track.name == track_name)

        total = int(db.scalar(count_query) or 0)
        items = list(
            db.scalars(
                data_query.order_by(Result.created_at.desc()).offset(offset).limit(limit)
            ).unique().all()
        )
        return items, total

    def get_by_id(self, db: Session, result_id: int) -> Result | None:
        query = select(Result).where(Result.id == result_id).options(
            joinedload(Result.player),
            joinedload(Result.race).joinedload(Race.track),
        )
        return db.scalars(query).unique().first()

    def get_by_race_and_player(self, db: Session, race_id: int, player_id: int) -> Result | None:
        query = select(Result).where(Result.race_id == race_id, Result.player_id == player_id)
        return db.scalars(query).first()

    def get_by_race_and_position(self, db: Session, race_id: int, finish_position: int) -> Result | None:
        query = select(Result).where(Result.race_id == race_id, Result.finish_position == finish_position)
        return db.scalars(query).first()

    def create(self, db: Session, result: Result) -> Result:
        db.add(result)
        db.flush()
        db.refresh(result)
        return result

    def delete(self, db: Session, result: Result) -> None:
        db.delete(result)
        db.flush()

    def list_by_race(self, db: Session, race_id: int) -> list[Result]:
        query = (
            select(Result)
            .where(Result.race_id == race_id)
            .options(joinedload(Result.player), joinedload(Result.race).joinedload(Race.track))
            .order_by(Result.finish_position.asc())
        )
        return list(db.scalars(query).unique().all())

    def list_by_player(self, db: Session, player_id: int) -> list[Result]:
        query = (
            select(Result)
            .where(Result.player_id == player_id)
            .options(joinedload(Result.player), joinedload(Result.race).joinedload(Race.track))
            .order_by(Result.created_at.desc())
        )
        return list(db.scalars(query).unique().all())
