from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class ExternalPlayerStatistic(TimestampMixin, Base):
    __tablename__ = "external_player_statistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(32), index=True, default="data_go", nullable=False)
    standard_year: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    racer_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    period_number: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    grade: Mapped[str] = mapped_column(String(20), index=True, default="unknown", nullable=False)
    run_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    run_day_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank1_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank2_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank3_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank4_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank5_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank6_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank7_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank8_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank9_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eliminated_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    win_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    high_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    high_3_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
