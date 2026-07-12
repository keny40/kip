from sqlalchemy.orm import Session

from app.models.tracks import Track
from app.repositories.tracks import TrackRepository
from app.schemas.tracks import TrackCreate, TrackUpdate


class TrackService:
    def __init__(self, repository: TrackRepository | None = None) -> None:
        self.repository = repository or TrackRepository()

    def list_tracks(self, db: Session) -> list[Track]:
        return self.repository.list_tracks(db)

    def get_track(self, db: Session, track_id: int) -> Track | None:
        return self.repository.get_by_id(db, track_id)

    def create_track(self, db: Session, payload: TrackCreate) -> Track:
        if self.repository.get_by_code(db, payload.code):
            raise ValueError("track code already exists")
        if self.repository.get_by_name(db, payload.name):
            raise ValueError("track name already exists")
        track = Track(**payload.model_dump())
        return self.repository.create(db, track)

    def update_track(self, db: Session, track_id: int, payload: TrackUpdate) -> Track:
        track = self.repository.get_by_id(db, track_id)
        if track is None:
            raise LookupError("track not found")
        updates = payload.model_dump(exclude_unset=True)
        if "code" in updates and updates["code"] != track.code and self.repository.get_by_code(db, updates["code"]):
            raise ValueError("track code already exists")
        if "name" in updates and updates["name"] != track.name and self.repository.get_by_name(db, updates["name"]):
            raise ValueError("track name already exists")
        for key, value in updates.items():
            setattr(track, key, value)
        db.flush()
        db.refresh(track)
        return track

    def delete_track(self, db: Session, track_id: int) -> None:
        track = self.repository.get_by_id(db, track_id)
        if track is None:
            raise LookupError("track not found")
        if track.races:
            raise ValueError("track has races")
        self.repository.delete(db, track)
