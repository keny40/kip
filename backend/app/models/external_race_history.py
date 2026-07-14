from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class ExternalRace(TimestampMixin, Base):
    __tablename__ = "external_races"
    __table_args__ = (
        UniqueConstraint(
            "source",
            "standard_year",
            "meet_name",
            "week_count",
            "day_count",
            "race_number",
            name="uq_external_races_natural_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    standard_year: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    meet_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    week_count: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    day_count: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    race_number: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    race_date: Mapped[date | None] = mapped_column(Date, index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="unknown", nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    entries = relationship("ExternalRaceEntry", back_populates="race", cascade="all, delete-orphan", lazy="selectin")
    results = relationship("ExternalRaceResult", back_populates="race", cascade="all, delete-orphan", lazy="selectin")


class ExternalRaceEntry(TimestampMixin, Base):
    __tablename__ = "external_race_entries"
    __table_args__ = (
        UniqueConstraint("external_race_id", "entry_number", name="uq_external_race_entries_race_entry"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_race_id: Mapped[int] = mapped_column(ForeignKey("external_races.id", ondelete="CASCADE"), index=True, nullable=False)
    entry_number: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    player_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    period_number: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    grade: Mapped[str] = mapped_column(String(20), index=True, default="unknown", nullable=False)
    external_player_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    race = relationship("ExternalRace", back_populates="entries", lazy="joined")


class ExternalRaceResult(TimestampMixin, Base):
    __tablename__ = "external_race_results"
    __table_args__ = (
        UniqueConstraint("external_race_id", "entry_number", name="uq_external_race_results_race_entry"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_race_id: Mapped[int] = mapped_column(ForeignKey("external_races.id", ondelete="CASCADE"), index=True, nullable=False)
    entry_number: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    player_name: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    period_number: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    result_rank: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    result_status: Mapped[str] = mapped_column(String(32), index=True, default="UNKNOWN_RESULT_STATUS", nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    race = relationship("ExternalRace", back_populates="results", lazy="joined")
