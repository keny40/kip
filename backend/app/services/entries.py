from sqlalchemy.orm import Session

from app.models.entries import Entry
from app.repositories.entries import EntryRepository
from app.repositories.players import PlayerRepository
from app.repositories.races import RaceRepository
from app.schemas.entries import EntryCreate


class EntryService:
    def __init__(
        self,
        repository: EntryRepository | None = None,
        race_repository: RaceRepository | None = None,
        player_repository: PlayerRepository | None = None,
    ) -> None:
        self.repository = repository or EntryRepository()
        self.race_repository = race_repository or RaceRepository()
        self.player_repository = player_repository or PlayerRepository()

    def create_entry(self, db: Session, payload: EntryCreate) -> Entry:
        race = self.race_repository.get_by_id(db, payload.race_id)
        if race is None:
            raise LookupError("race not found")
        player = self.player_repository.get_by_id(db, payload.player_id)
        if player is None:
            raise LookupError("player not found")
        if self.repository.get_by_race_and_entry_number(db, payload.race_id, payload.entry_number):
            raise ValueError("entry_number already exists in race")
        if self.repository.get_by_race_and_player(db, payload.race_id, payload.player_id):
            raise ValueError("race_id and player_id already exists")
        entry = Entry(**payload.model_dump())
        return self.repository.create(db, entry)
