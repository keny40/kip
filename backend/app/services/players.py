from sqlalchemy.orm import Session

from app.models.players import Player
from app.repositories.players import PlayerRepository
from app.schemas.players import PlayerCreate


class PlayerService:
    def __init__(self, repository: PlayerRepository | None = None) -> None:
        self.repository = repository or PlayerRepository()

    def list_players(self, db: Session, *, page: int, page_size: int) -> tuple[list[Player], int]:
        offset = (page - 1) * page_size
        return self.repository.list_players(db, offset=offset, limit=page_size)

    def get_player(self, db: Session, player_id: int) -> Player | None:
        return self.repository.get_by_id(db, player_id)

    def create_player(self, db: Session, payload: PlayerCreate) -> Player:
        if self.repository.get_by_player_number(db, payload.player_number):
            raise ValueError("player_number already exists")
        player = Player(**payload.model_dump())
        return self.repository.create(db, player)
