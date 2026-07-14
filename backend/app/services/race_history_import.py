from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.external_race_history import ExternalRace, ExternalRaceEntry, ExternalRaceResult


@dataclass
class RaceHistoryImportReport:
    races_created: int = 0
    races_updated: int = 0
    races_skipped: int = 0
    entries_created: int = 0
    entries_updated: int = 0
    entries_skipped: int = 0
    results_created: int = 0
    results_updated: int = 0
    results_skipped: int = 0
    failed: int = 0
    issues: list[dict[str, str]] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "races_created": self.races_created,
            "races_updated": self.races_updated,
            "races_skipped": self.races_skipped,
            "entries_created": self.entries_created,
            "entries_updated": self.entries_updated,
            "entries_skipped": self.entries_skipped,
            "results_created": self.results_created,
            "results_updated": self.results_updated,
            "results_skipped": self.results_skipped,
            "failed": self.failed,
            "issues": self.issues or [],
        }


class RaceHistoryImportService:
    def import_preview(self, db: Session, payload: dict[str, Any], *, dry_run: bool = True) -> RaceHistoryImportReport:
        report = RaceHistoryImportReport(issues=[])
        for index, race_payload in enumerate(payload.get("races", []), start=1):
            try:
                self._import_race(db, race_payload, report, dry_run=dry_run)
            except ValueError as exc:
                report.failed += 1
                report.issues.append({"row": str(index), "error_code": str(exc)})
        if dry_run:
            db.rollback()
        return report

    def _import_race(self, db: Session, race_payload: dict[str, Any], report: RaceHistoryImportReport, *, dry_run: bool) -> None:
        source = str(race_payload.get("source") or "data_go")
        standard_year = _required_str(race_payload, "standard_year")
        meet_name = _required_str(race_payload, "meet_name")
        week_count = _required_int(race_payload, "week_count")
        day_count = _required_int(race_payload, "day_count")
        race_number = _required_str(race_payload, "race_number")
        collected_at_present = _has_value(race_payload.get("collected_at"))
        collected_at = _parse_datetime(race_payload.get("collected_at"))
        race = db.scalar(
            select(ExternalRace).where(
                ExternalRace.source == source,
                ExternalRace.standard_year == standard_year,
                ExternalRace.meet_name == meet_name,
                ExternalRace.week_count == week_count,
                ExternalRace.day_count == day_count,
                ExternalRace.race_number == race_number,
            )
        )
        race_values = {
            "race_date": _parse_date(race_payload.get("race_date")),
            "status": str(race_payload.get("status") or "unknown"),
            "collected_at": collected_at,
        }
        if race is None:
            report.races_created += 1
            if not dry_run:
                race = ExternalRace(
                    source=source,
                    standard_year=standard_year,
                    meet_name=meet_name,
                    week_count=week_count,
                    day_count=day_count,
                    race_number=race_number,
                    **race_values,
                )
                db.add(race)
                db.flush()
        else:
            changed = _changed_fields(race, _comparison_values(race_values, include_collected_at=collected_at_present))
            if changed:
                report.races_updated += 1
                if not dry_run:
                    for key, value in _comparison_values(race_values, include_collected_at=collected_at_present).items():
                        setattr(race, key, value)
            else:
                report.races_skipped += 1
        if race is None and dry_run:
            race_id = -1
        else:
            race_id = race.id
        for entry_payload in race_payload.get("entries", []):
            self._upsert_entry(db, race_id, entry_payload, collected_at, collected_at_present, report, dry_run=dry_run)
        for result_payload in race_payload.get("results", []):
            self._upsert_result(db, race_id, result_payload, collected_at, collected_at_present, report, dry_run=dry_run)

    def _upsert_entry(self, db, race_id: int, payload: dict[str, Any], collected_at: datetime, collected_at_present: bool, report: RaceHistoryImportReport, *, dry_run: bool) -> None:
        entry_number = _required_str(payload, "entry_number")
        values = {
            "player_name": _required_str(payload, "player_name"),
            "period_number": _optional_str(payload.get("period_number")),
            "grade": _optional_str(payload.get("grade")) or "unknown",
            "external_player_id": _optional_str(payload.get("external_player_id")),
            "collected_at": collected_at,
        }
        existing = None if dry_run else db.scalar(select(ExternalRaceEntry).where(ExternalRaceEntry.external_race_id == race_id, ExternalRaceEntry.entry_number == entry_number))
        if existing is None:
            report.entries_created += 1
            if not dry_run:
                db.add(ExternalRaceEntry(external_race_id=race_id, entry_number=entry_number, **values))
        else:
            changed = _changed_fields(existing, _comparison_values(values, include_collected_at=collected_at_present))
            if changed:
                report.entries_updated += 1
                if not dry_run:
                    for key, value in _comparison_values(values, include_collected_at=collected_at_present).items():
                        setattr(existing, key, value)
            else:
                report.entries_skipped += 1

    def _upsert_result(self, db, race_id: int, payload: dict[str, Any], collected_at: datetime, collected_at_present: bool, report: RaceHistoryImportReport, *, dry_run: bool) -> None:
        entry_number = _required_str(payload, "entry_number")
        status = _normal_result_status(payload)
        values = {
            "player_name": _optional_str(payload.get("player_name")),
            "period_number": _optional_str(payload.get("period_number")),
            "result_rank": _optional_int(payload.get("result_rank")),
            "result_status": status,
            "collected_at": collected_at,
        }
        existing = None if dry_run else db.scalar(select(ExternalRaceResult).where(ExternalRaceResult.external_race_id == race_id, ExternalRaceResult.entry_number == entry_number))
        if existing is None:
            report.results_created += 1
            if not dry_run:
                db.add(ExternalRaceResult(external_race_id=race_id, entry_number=entry_number, **values))
        else:
            changed = _changed_fields(existing, _comparison_values(values, include_collected_at=collected_at_present))
            if changed:
                report.results_updated += 1
                if not dry_run:
                    for key, value in _comparison_values(values, include_collected_at=collected_at_present).items():
                        setattr(existing, key, value)
            else:
                report.results_skipped += 1


def _comparison_values(values: dict[str, Any], *, include_collected_at: bool) -> dict[str, Any]:
    if include_collected_at:
        return values
    return {key: value for key, value in values.items() if key != "collected_at"}


def _changed_fields(model, values: dict[str, Any]) -> list[str]:
    return [key for key, value in values.items() if not _same_value(getattr(model, key), value)]


def _same_value(left: Any, right: Any) -> bool:
    if isinstance(left, datetime) and isinstance(right, datetime):
        return left.replace(tzinfo=None) == right.replace(tzinfo=None)
    return left == right


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if value is None or str(value).strip() == "":
        raise ValueError(f"MISSING_{key.upper()}")
    return str(value).strip()


def _has_value(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _required_int(payload: dict[str, Any], key: str) -> int:
    value = _required_str(payload, key)
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"INVALID_{key.upper()}") from exc


def _optional_str(value: Any) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    return str(value).strip()


def _optional_int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError("INVALID_RESULT_RANK") from exc


def _parse_date(value: Any) -> date | None:
    text = _optional_str(value)
    if not text:
        return None
    if len(text) == 8 and text.isdigit():
        return date(int(text[:4]), int(text[4:6]), int(text[6:]))
    return date.fromisoformat(text)


def _parse_datetime(value: Any) -> datetime:
    text = _optional_str(value)
    if not text:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _normal_result_status(payload: dict[str, Any]) -> str:
    raw = _optional_str(payload.get("result_status"))
    if raw:
        normalized = raw.upper()
        if normalized in {"FINISHED", "WITHDRAWN", "DISQUALIFIED", "DID_NOT_START", "UNKNOWN_RESULT_STATUS"}:
            return normalized
    rank = _optional_int(payload.get("result_rank"))
    return "FINISHED" if rank is not None else "UNKNOWN_RESULT_STATUS"
