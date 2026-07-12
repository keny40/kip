from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tracks import Track


class TrackRepository:
    def list_tracks(self, db: Session) -> list[Track]:
        return list(db.scalars(select(Track).order_by(Track.name.asc())).all())

    def get_by_id(self, db: Session, track_id: int) -> Track | None:
        return db.get(Track, track_id)

    def get_by_code(self, db: Session, code: str) -> Track | None:
        return db.scalars(select(Track).where(Track.code == code)).first()

    def get_by_name(self, db: Session, name: str) -> Track | None:
        return db.scalars(select(Track).where(Track.name == name)).first()

    def create(self, db: Session, track: Track) -> Track:
        db.add(track)
        db.flush()
        db.refresh(track)
        return track

    def delete(self, db: Session, track: Track) -> None:
        db.delete(track)
        db.flush()
