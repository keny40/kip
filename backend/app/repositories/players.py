from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.players import Player


class PlayerRepository:
    def list_players(self, db: Session, offset: int, limit: int) -> tuple[list[Player], int]:
        total = db.scalar(select(func.count()).select_from(Player)) or 0
        query = select(Player).order_by(Player.player_number.asc()).offset(offset).limit(limit)
        items = list(db.scalars(query).all())
        return items, int(total)

    def get_by_id(self, db: Session, player_id: int) -> Player | None:
        return db.get(Player, player_id)

    def get_by_player_number(self, db: Session, player_number: int) -> Player | None:
        query = select(Player).where(Player.player_number == player_number)
        return db.scalars(query).first()

    def create(self, db: Session, player: Player) -> Player:
        db.add(player)
        db.flush()
        db.refresh(player)
        return player
