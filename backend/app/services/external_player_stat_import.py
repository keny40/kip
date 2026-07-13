from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.data_go_player_stats import CollectedPlayerStatistic
from app.models.external_player_statistics import ExternalPlayerStatistic


STAT_VALUE_FIELDS = (
    "grade",
    "run_count",
    "run_day_count",
    "rank1_count",
    "rank2_count",
    "rank3_count",
    "rank4_count",
    "rank5_count",
    "rank6_count",
    "rank7_count",
    "rank8_count",
    "rank9_count",
    "eliminated_count",
    "win_rate",
    "high_rate",
    "high_3_rate",
)


@dataclass(frozen=True)
class PlayerStatImportPreview:
    action: str
    racer_name: str
    period_number: str | None
    standard_year: str
    changed_fields: tuple[str, ...] = ()


@dataclass
class PlayerStatImportReport:
    total_rows: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    preview: list[PlayerStatImportPreview] = field(default_factory=list)


class ExternalPlayerStatisticImportService:
    def upsert(
        self,
        db: Session,
        rows: list[CollectedPlayerStatistic],
        *,
        dry_run: bool,
    ) -> PlayerStatImportReport:
        report = PlayerStatImportReport(total_rows=len(rows))
        for row in rows:
            existing = self._find_existing(db, row)
            if existing is None:
                report.created += 1
                report.preview.append(
                    PlayerStatImportPreview(
                        "created", row.racer_name, row.period_number, row.standard_year
                    )
                )
                if not dry_run:
                    db.add(ExternalPlayerStatistic(**row.__dict__))
                continue

            changed_fields = tuple(
                field_name
                for field_name in STAT_VALUE_FIELDS
                if getattr(existing, field_name) != getattr(row, field_name)
            )
            if not changed_fields:
                report.skipped += 1
                report.preview.append(
                    PlayerStatImportPreview(
                        "skipped", row.racer_name, row.period_number, row.standard_year
                    )
                )
                continue

            report.updated += 1
            report.preview.append(
                PlayerStatImportPreview(
                    "updated",
                    row.racer_name,
                    row.period_number,
                    row.standard_year,
                    changed_fields,
                )
            )
            if not dry_run:
                for field_name in changed_fields:
                    setattr(existing, field_name, getattr(row, field_name))
                existing.collected_at = row.collected_at

        if not dry_run:
            db.flush()
        return report

    def _find_existing(
        self,
        db: Session,
        row: CollectedPlayerStatistic,
    ) -> ExternalPlayerStatistic | None:
        period_filter = (
            ExternalPlayerStatistic.period_number.is_(None)
            if row.period_number is None
            else ExternalPlayerStatistic.period_number == row.period_number
        )
        query = select(ExternalPlayerStatistic).where(
            ExternalPlayerStatistic.source == row.source,
            ExternalPlayerStatistic.standard_year == row.standard_year,
            ExternalPlayerStatistic.racer_name == row.racer_name,
            period_filter,
        )
        return db.scalars(query).first()
