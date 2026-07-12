from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EntryStatus
from app.models.mixins import TimestampMixin


class Entry(TimestampMixin, Base):
    __tablename__ = "entries"
    __table_args__ = (
        UniqueConstraint("race_id", "entry_number", name="uq_entries_race_entry_number"),
        UniqueConstraint("race_id", "player_id", name="uq_entries_race_player"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    race_id: Mapped[int] = mapped_column(ForeignKey("races.id", ondelete="CASCADE"), index=True, nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="RESTRICT"), index=True, nullable=False)
    entry_number: Mapped[int] = mapped_column(Integer, nullable=False)
    lane_number: Mapped[int] = mapped_column(Integer, nullable=False)
    lineup_position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, default=EntryStatus.confirmed.value, nullable=False)
    race = relationship("Race", back_populates="entries", lazy="joined")
    player = relationship("Player", back_populates="entries", lazy="joined")
