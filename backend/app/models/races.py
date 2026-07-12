from datetime import date, time

from sqlalchemy import Date, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import RaceStatus
from app.models.mixins import TimestampMixin


class Race(TimestampMixin, Base):
    __tablename__ = "races"
    __table_args__ = (
        UniqueConstraint("race_date", "track_id", "race_number", name="uq_races_date_track_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    race_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id", ondelete="RESTRICT"), index=True, nullable=False)
    race_number: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    scheduled_start_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, default=RaceStatus.scheduled.value, nullable=False)
    entries = relationship("Entry", back_populates="race", cascade="all, delete-orphan", lazy="selectin")
    results = relationship("Result", back_populates="race", cascade="all, delete-orphan", lazy="selectin")
    track = relationship("Track", back_populates="races", lazy="joined")

    @property
    def track_name(self) -> str:
        return self.track.name if self.track is not None else ""
