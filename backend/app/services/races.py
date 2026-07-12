from sqlalchemy.orm import Session

from app.models.races import Race
from app.repositories.races import RaceRepository
from app.repositories.tracks import TrackRepository
from app.schemas.races import RaceCreate


class RaceService:
    def __init__(self, repository: RaceRepository | None = None) -> None:
        self.repository = repository or RaceRepository()
        self.track_repository = TrackRepository()

    def list_races(
        self,
        db: Session,
        *,
        race_date=None,
        track_name: str | None = None,
        status: str | None = None,
        page: int,
        page_size: int,
    ) -> tuple[list[Race], int]:
        offset = (page - 1) * page_size
        return self.repository.list_races(
            db,
            race_date=race_date,
            track_name=track_name,
            status=status,
            offset=offset,
            limit=page_size,
        )

    def get_race(self, db: Session, race_id: int) -> Race | None:
        return self.repository.get_by_id(db, race_id)

    def create_race(self, db: Session, payload: RaceCreate) -> Race:
        track = None
        if payload.track_id is not None:
            track = self.track_repository.get_by_id(db, payload.track_id)
            if track is None:
                raise LookupError("track not found")
            if payload.track_name is not None and payload.track_name != track.name:
                raise ValueError("track_id and track_name do not match")
        else:
            track = self.track_repository.get_by_name(db, payload.track_name or "")
            if track is None:
                raise LookupError("track not found")

        if self.repository.get_duplicate(db, payload.race_date, track.id, payload.race_number):
            raise ValueError("duplicate race")
        race = Race(
            race_date=payload.race_date,
            track_id=track.id,
            race_number=payload.race_number,
            scheduled_start_time=payload.scheduled_start_time,
            status=payload.status,
        )
        return self.repository.create(db, race)
