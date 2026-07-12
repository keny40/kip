from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PlayerStatus
from app.models.mixins import TimestampMixin


class Player(TimestampMixin, Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    player_number: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    grade: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    region: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, default=PlayerStatus.active.value, nullable=False)
    entries = relationship("Entry", back_populates="player", cascade="all, delete-orphan", lazy="selectin")
    results = relationship("Result", back_populates="player", cascade="all, delete-orphan", lazy="selectin")
