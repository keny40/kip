from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class ExternalPlayer(TimestampMixin, Base):
    __tablename__ = "external_players"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_external_players_source_external_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    external_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    period_number: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    grade: Mapped[str] = mapped_column(String(20), index=True, default="unknown", nullable=False)
    region: Mapped[str] = mapped_column(String(100), index=True, default="unknown", nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, default="unknown", nullable=False)
    detail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
