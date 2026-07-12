from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ResultStatus
from app.models.mixins import TimestampMixin


class Result(TimestampMixin, Base):
    __tablename__ = "results"
    __table_args__ = (
        UniqueConstraint("race_id", "player_id", name="uq_results_race_player"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    race_id: Mapped[int] = mapped_column(ForeignKey("races.id", ondelete="CASCADE"), index=True, nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="RESTRICT"), index=True, nullable=False)
    finish_position: Mapped[int] = mapped_column(Integer, nullable=False)
    finish_time: Mapped[str | None] = mapped_column(String(50), nullable=True)
    result_status: Mapped[str] = mapped_column(String(32), index=True, default=ResultStatus.finished.value, nullable=False)
    points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    race = relationship("Race", back_populates="results", lazy="joined")
    player = relationship("Player", back_populates="results", lazy="joined")
