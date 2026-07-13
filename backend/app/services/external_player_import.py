from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import re
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.external_players import ExternalPlayer
from app.repositories.external_players import ExternalPlayerRepository


EXPECTED_COLUMNS = (
    "external_id",
    "name",
    "period_number",
    "grade",
    "region",
    "status",
    "detail_url",
    "source",
    "collected_at",
)
UPSERT_FIELDS = (
    "name",
    "period_number",
    "grade",
    "region",
    "status",
    "detail_url",
    "collected_at",
)


@dataclass(frozen=True)
class ExternalPlayerImportIssue:
    row_number: int
    error_code: str
    message: str


@dataclass(frozen=True)
class ExternalPlayerImportPreview:
    action: str
    source: str
    external_id: str
    name: str
    changed_fields: tuple[str, ...] = ()


@dataclass
class ExternalPlayerImportReport:
    total_rows: int = 0
    valid_rows: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    duplicate_rows: int = 0
    issues: list[ExternalPlayerImportIssue] = field(default_factory=list)
    preview: list[ExternalPlayerImportPreview] = field(default_factory=list)


@dataclass(frozen=True)
class _ValidatedExternalPlayerRow:
    row_number: int
    source: str
    external_id: str
    name: str
    period_number: str | None
    grade: str
    region: str
    status: str
    detail_url: str | None
    collected_at: datetime


class ExternalPlayerCSVImportService:
    def __init__(self, repository: ExternalPlayerRepository | None = None) -> None:
        self.repository = repository or ExternalPlayerRepository()

    def import_csv(
        self,
        db: Session,
        csv_path: Path,
        *,
        dry_run: bool,
    ) -> ExternalPlayerImportReport:
        report = ExternalPlayerImportReport()
        rows = self._read_and_validate(csv_path, report)
        seen: set[tuple[str, str]] = set()

        for row in rows:
            key = (row.source, row.external_id)
            if key in seen:
                report.duplicate_rows += 1
                report.skipped += 1
                continue
            seen.add(key)
            report.valid_rows += 1

            existing = self.repository.get_by_source_external_id(
                db,
                source=row.source,
                external_id=row.external_id,
            )
            if existing is None:
                report.created += 1
                report.preview.append(
                    ExternalPlayerImportPreview(
                        action="created",
                        source=row.source,
                        external_id=row.external_id,
                        name=row.name,
                    )
                )
                if not dry_run:
                    db.add(
                        ExternalPlayer(
                            source=row.source,
                            external_id=row.external_id,
                            name=row.name,
                            period_number=row.period_number,
                            grade=row.grade,
                            region=row.region,
                            status=row.status,
                            detail_url=row.detail_url,
                            source_updated_at=None,
                            collected_at=row.collected_at,
                        )
                    )
                continue

            changed_fields = tuple(
                field_name
                for field_name in UPSERT_FIELDS
                if not _values_equal(field_name, getattr(existing, field_name), getattr(row, field_name))
            )
            if not changed_fields:
                report.skipped += 1
                report.preview.append(
                    ExternalPlayerImportPreview(
                        action="skipped",
                        source=row.source,
                        external_id=row.external_id,
                        name=row.name,
                    )
                )
                continue

            report.updated += 1
            report.preview.append(
                ExternalPlayerImportPreview(
                    action="updated",
                    source=row.source,
                    external_id=row.external_id,
                    name=row.name,
                    changed_fields=changed_fields,
                )
            )
            if not dry_run:
                for field_name in changed_fields:
                    setattr(existing, field_name, getattr(row, field_name))

        if not dry_run:
            db.flush()
        return report

    def _read_and_validate(
        self,
        csv_path: Path,
        report: ExternalPlayerImportReport,
    ) -> list[_ValidatedExternalPlayerRow]:
        validated: list[_ValidatedExternalPlayerRow] = []
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError("CSV has no header row")
            actual_columns = tuple(column.strip() for column in reader.fieldnames)
            if actual_columns != EXPECTED_COLUMNS:
                raise ValueError(
                    f"Invalid CSV header. Expected {list(EXPECTED_COLUMNS)}, got {list(actual_columns)}"
                )

            for row_number, raw in enumerate(reader, start=2):
                report.total_rows += 1
                try:
                    validated.append(_validate_row(row_number, raw))
                except ValueError as exc:
                    report.failed += 1
                    report.issues.append(
                        ExternalPlayerImportIssue(
                            row_number=row_number,
                            error_code="VALIDATION_ERROR",
                            message=str(exc),
                        )
                    )
        return validated


def _validate_row(row_number: int, raw: dict[str, str]) -> _ValidatedExternalPlayerRow:
    source = _required(raw, "source").lower()
    if source != "kcycle":
        raise ValueError("source must be kcycle")

    external_id = _required(raw, "external_id")
    if not re.fullmatch(r"\d{8}", external_id):
        raise ValueError("KCYCLE external_id must be an 8-digit string")
    name = _required(raw, "name")
    period_number = _optional(raw.get("period_number"))
    grade = _optional(raw.get("grade")) or "unknown"
    region = _optional(raw.get("region")) or "unknown"
    status = _optional(raw.get("status")) or "unknown"
    detail_url = _optional(raw.get("detail_url"))
    if detail_url and urlparse(detail_url).path.rsplit("/", 1)[-1] != external_id:
        raise ValueError("detail_url must end with the same external_id")
    collected_at = _parse_datetime(_required(raw, "collected_at"))

    return _ValidatedExternalPlayerRow(
        row_number=row_number,
        source=source,
        external_id=external_id,
        name=name,
        period_number=period_number,
        grade=grade,
        region=region,
        status=status,
        detail_url=detail_url,
        collected_at=collected_at,
    )


def _required(raw: dict[str, str], field_name: str) -> str:
    value = _optional(raw.get(field_name))
    if value is None:
        raise ValueError(f"Missing required field: {field_name}")
    return value


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _parse_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("collected_at must be an ISO-8601 datetime") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _canonical_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _values_equal(field_name: str, left, right) -> bool:
    if field_name == "collected_at":
        return _canonical_datetime(left) == _canonical_datetime(right)
    return left == right
