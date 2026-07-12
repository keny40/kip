from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.entries import Entry


class EntryRepository:
    def get_by_race_and_entry_number(self, db: Session, race_id: int, entry_number: int) -> Entry | None:
        query = select(Entry).where(Entry.race_id == race_id, Entry.entry_number == entry_number)
        return db.scalars(query).first()

    def get_by_race_and_player(self, db: Session, race_id: int, player_id: int) -> Entry | None:
        query = select(Entry).where(Entry.race_id == race_id, Entry.player_id == player_id)
        return db.scalars(query).first()

    def create(self, db: Session, entry: Entry) -> Entry:
        db.add(entry)
        db.flush()
        db.refresh(entry)
        return entry

    def list_by_race(self, db: Session, race_id: int) -> list[Entry]:
        query = (
            select(Entry)
            .where(Entry.race_id == race_id)
            .options(joinedload(Entry.player))
            .order_by(Entry.entry_number.asc())
        )
        return list(db.scalars(query).all())
