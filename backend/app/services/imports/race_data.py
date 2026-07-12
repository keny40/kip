from __future__ import annotations

from collections.abc import Callable
from csv import DictReader
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.schemas.entries import EntryCreate
from app.schemas.players import PlayerCreate
from app.schemas.races import RaceCreate
from app.schemas.results import ResultCreate
from app.services.entries import EntryService
from app.services.tracks import TrackService
from app.services.players import PlayerService
from app.services.races import RaceService
from app.services.results import ResultService
from app.schemas.tracks import TrackCreate


@dataclass
class ImportIssue:
    row_number: int
    import_type: str
    raw_data: dict[str, str]
    error_code: str
    error_message: str


@dataclass
class ImportReport:
    entity: str
    created: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)
    issues: list[ImportIssue] = field(default_factory=list)


def _normalize_columns(columns: list[str]) -> list[str]:
    return [column.strip() for column in columns]


def _validate_headers(expected: list[str], actual: list[str]) -> None:
    if _normalize_columns(expected) != _normalize_columns(actual):
        raise ValueError(f"Invalid CSV header. Expected: {expected}, got: {actual}")


def _validate_any_headers(expected_options: list[list[str]], actual: list[str]) -> list[str]:
    normalized_actual = _normalize_columns(actual)
    for expected in expected_options:
        if _normalize_columns(expected) == normalized_actual:
            return expected
    raise ValueError(f"Invalid CSV header. Expected one of: {expected_options}, got: {actual}")


def _parse_date(value: str) -> date:
    return date.fromisoformat(value.strip())


def _parse_time(value: str) -> time:
    return time.fromisoformat(value.strip())


def _parse_int(value: str) -> int:
    return int(value.strip())


def _parse_optional_int(value: str | None) -> int | None:
    if value is None or value.strip() == "":
        return None
    return int(value.strip())


def _parse_row(row: dict[str, str], key: str) -> str:
    value = row.get(key)
    if value is None or value.strip() == "":
        raise ValueError(f"Missing required field: {key}")
    return value.strip()


class CSVImportService:
    def __init__(
        self,
        *,
        player_service: PlayerService | None = None,
        race_service: RaceService | None = None,
        entry_service: EntryService | None = None,
        result_service: ResultService | None = None,
    ) -> None:
        self.player_service = player_service or PlayerService()
        self.race_service = race_service or RaceService()
        self.entry_service = entry_service or EntryService()
        self.result_service = result_service or ResultService()
        self.track_service = TrackService()

    def import_tracks(self, db: Session, csv_path: Path, dry_run: bool = False) -> ImportReport:
        expected = ["code", "name", "region", "address", "status"]
        return self._import_rows(db, csv_path, expected, "tracks", dry_run, self._import_track_row)

    def import_players(self, db: Session, csv_path: Path, dry_run: bool = False) -> ImportReport:
        expected = ["player_number", "name", "grade", "region", "status"]
        return self._import_rows(
            db,
            csv_path,
            expected,
            "players",
            dry_run,
            self._import_player_row,
        )

    def import_races(self, db: Session, csv_path: Path, dry_run: bool = False) -> ImportReport:
        expected_options = [
            ["race_date", "track_code", "race_number", "scheduled_start_time", "status"],
            ["race_date", "track_name", "race_number", "scheduled_start_time", "status"],
        ]
        return self._import_rows(db, csv_path, expected_options, "races", dry_run, self._import_race_row)

    def import_entries(self, db: Session, csv_path: Path, dry_run: bool = False) -> ImportReport:
        expected = [
            "race_date",
            "track_code",
            "race_number",
            "player_number",
            "entry_number",
            "lane_number",
            "lineup_position",
            "status",
        ]
        return self._import_rows(db, csv_path, expected, "entries", dry_run, self._import_entry_row)

    def import_results(self, db: Session, csv_path: Path, dry_run: bool = False) -> ImportReport:
        expected = [
            "race_date",
            "track_code",
            "race_number",
            "player_number",
            "finish_position",
            "finish_time",
            "result_status",
            "points",
        ]
        return self._import_rows(db, csv_path, expected, "results", dry_run, self._import_result_row)

    def _import_rows(
        self,
        db: Session,
        csv_path: Path,
        expected_columns: list[str] | list[list[str]],
        entity: str,
        dry_run: bool,
        handler: Callable[[Session, dict[str, str]], None],
    ) -> ImportReport:
        report = ImportReport(entity=entity)
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError(f"{csv_path} has no header row")
            if expected_columns and isinstance(expected_columns[0], list):
                _validate_any_headers(expected_columns, reader.fieldnames)  # type: ignore[arg-type]
            else:
                _validate_headers(expected_columns, reader.fieldnames)  # type: ignore[arg-type]

            for row_number, row in enumerate(reader, start=2):
                try:
                    with db.begin_nested():
                        handler(db, row)
                        report.created += 1
                except LookupError as exc:
                    report.failed += 1
                    message = str(exc)
                    report.errors.append(message)
                    report.issues.append(
                        ImportIssue(
                            row_number=row_number,
                            import_type=entity,
                            raw_data=row,
                            error_code="lookup_error",
                            error_message=message,
                        )
                    )
                except ValueError as exc:
                    message = str(exc)
                    if "already exists" in message or "duplicate" in message:
                        report.skipped += 1
                    else:
                        report.failed += 1
                        report.errors.append(message)
                        report.issues.append(
                            ImportIssue(
                                row_number=row_number,
                                import_type=entity,
                                raw_data=row,
                                error_code="validation_error",
                                error_message=message,
                            )
                        )
                except Exception as exc:  # pragma: no cover - defensive
                    report.failed += 1
                    message = f"Unexpected error: {exc}"
                    report.errors.append(message)
                    report.issues.append(
                        ImportIssue(
                            row_number=row_number,
                            import_type=entity,
                            raw_data=row,
                            error_code="unexpected_error",
                            error_message=message,
                        )
                    )

        if dry_run:
            db.rollback()
        return report

    def _import_player_row(self, db: Session, row: dict[str, str]) -> None:
        player = PlayerCreate(
            player_number=_parse_int(_parse_row(row, "player_number")),
            name=_parse_row(row, "name"),
            grade=_parse_row(row, "grade"),
            region=_parse_row(row, "region"),
            status=_parse_row(row, "status"),
        )
        self.player_service.create_player(db, player)

    def _import_track_row(self, db: Session, row: dict[str, str]) -> None:
        track = TrackCreate(
            code=_parse_row(row, "code"),
            name=_parse_row(row, "name"),
            region=_parse_row(row, "region"),
            address=row.get("address", "").strip() or None,
            status=_parse_row(row, "status"),
        )
        self.track_service.create_track(db, track)

    def _import_race_row(self, db: Session, row: dict[str, str]) -> None:
        track = self._resolve_track(db, row)
        race = RaceCreate(
            race_date=_parse_date(_parse_row(row, "race_date")),
            track_id=track.id,
            track_name=track.name,
            race_number=_parse_int(_parse_row(row, "race_number")),
            scheduled_start_time=_parse_time(_parse_row(row, "scheduled_start_time")),
            status=_parse_row(row, "status"),
        )
        self.race_service.create_race(db, race)

    def _resolve_track(self, db: Session, row: dict[str, str]):
        track_code = row.get("track_code", "").strip()
        track_name = row.get("track_name", "").strip()
        track = None
        if track_code:
            track = self.track_service.repository.get_by_code(db, track_code)
        if track is None and track_name:
            track = self.track_service.repository.get_by_name(db, track_name)
        if track_code and track_name and track and track.code != track_code:
            raise ValueError("track_code and track_name do not match")
        if track is None:
            raise LookupError("track not found")
        return track

    def _lookup_race_id(self, db: Session, row: dict[str, str]) -> int:
        race_date = _parse_date(_parse_row(row, "race_date"))
        track = self._resolve_track(db, row)
        race_number = _parse_int(_parse_row(row, "race_number"))
        race = self.race_service.repository.get_duplicate(db, race_date, track.id, race_number)
        if race is None:
            raise LookupError(f"Race not found for {race_date} / {track.name} / {race_number}")
        return race.id

    def _lookup_player_id(self, db: Session, player_number: int) -> int:
        player = self.player_service.repository.get_by_player_number(db, player_number)
        if player is None:
            raise LookupError(f"Player not found for player_number={player_number}")
        return player.id

    def _import_entry_row(self, db: Session, row: dict[str, str]) -> None:
        race_id = self._lookup_race_id(db, row)
        player_id = self._lookup_player_id(db, _parse_int(_parse_row(row, "player_number")))
        entry = EntryCreate(
            race_id=race_id,
            player_id=player_id,
            entry_number=_parse_int(_parse_row(row, "entry_number")),
            lane_number=_parse_int(_parse_row(row, "lane_number")),
            lineup_position=_parse_int(_parse_row(row, "lineup_position")),
            status=_parse_row(row, "status"),
        )
        self.entry_service.create_entry(db, entry)

    def _import_result_row(self, db: Session, row: dict[str, str]) -> None:
        race_id = self._lookup_race_id(db, row)
        player_id = self._lookup_player_id(db, _parse_int(_parse_row(row, "player_number")))
        result = ResultCreate(
            race_id=race_id,
            player_id=player_id,
            finish_position=_parse_int(_parse_row(row, "finish_position")),
            finish_time=row.get("finish_time", "").strip() or None,
            result_status=_parse_row(row, "result_status"),
            points=_parse_optional_int(row.get("points")),
        )
        self.result_service.create_result(db, result)
