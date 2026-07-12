from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.session import get_engine
from app.schemas.imports import ImportErrorRead, ImportResponseRead, ImportType
from app.services.imports.race_data import CSVImportService, ImportIssue, ImportReport

ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "text/plain",
}

REQUIRED_COLUMNS = {
    ImportType.tracks: ["code", "name", "region", "address", "status"],
    ImportType.players: ["player_number", "name", "grade", "region", "status"],
    ImportType.races: ["race_date", "track_code", "race_number", "scheduled_start_time", "status"],
    ImportType.entries: [
        "race_date",
        "track_code",
        "race_number",
        "player_number",
        "entry_number",
        "lane_number",
        "lineup_position",
        "status",
    ],
    ImportType.results: [
        "race_date",
        "track_code",
        "race_number",
        "player_number",
        "finish_position",
        "finish_time",
        "result_status",
        "points",
    ],
}


class CSVUploadService:
    def __init__(self, importer: CSVImportService | None = None) -> None:
        self.importer = importer or CSVImportService()

    def import_upload(
        self,
        db: Session,
        *,
        import_type: ImportType,
        upload_file: UploadFile,
        dry_run: bool = False,
    ) -> ImportResponseRead:
        filename = Path(upload_file.filename or "upload.csv").name
        self._validate_upload(upload_file, filename)

        data = upload_file.file.read(settings.csv_import_max_bytes + 1)
        if not data:
            raise ValueError("CSV file is empty")
        if len(data) > settings.csv_import_max_bytes:
            raise OverflowError(f"CSV file exceeds maximum size of {settings.csv_import_max_bytes} bytes")

        try:
            data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("CSV file must be UTF-8 encoded") from exc

        temp_path: Path | None = None
        dry_run_session: Session | None = None
        dry_run_resource: object | None = None
        dry_run_temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile("wb", suffix=".csv", delete=False) as handle:
                temp_path = Path(handle.name)
                handle.write(data)

            working_db = db
            if dry_run:
                working_db, dry_run_resource, dry_run_temp_path = self._create_dry_run_session(db)
                dry_run_session = working_db

            try:
                report = self._dispatch_import(working_db, import_type, temp_path, dry_run)
            finally:
                if dry_run_session is not None:
                    dry_run_session.rollback()
                    dry_run_session.close()
                if dry_run_resource is not None:
                    self._cleanup_dry_run_resource(dry_run_resource)
                if dry_run_temp_path is not None and dry_run_temp_path.exists():
                    dry_run_temp_path.unlink(missing_ok=True)

            return self._to_response(report, import_type, filename, dry_run)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink(missing_ok=True)
            upload_file.file.close()

    def _validate_upload(self, upload_file: UploadFile, filename: str) -> None:
        if not filename.lower().endswith(".csv"):
            raise ValueError("Only .csv files are allowed")
        if upload_file.content_type and upload_file.content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError("Unsupported CSV content type")

    def _dispatch_import(self, db: Session, import_type: ImportType, csv_path: Path, dry_run: bool) -> ImportReport:
        if import_type == ImportType.tracks:
            self._validate_required_columns(csv_path, REQUIRED_COLUMNS[ImportType.tracks])
            return self.importer.import_tracks(db, csv_path, dry_run=dry_run)
        if import_type == ImportType.players:
            self._validate_required_columns(csv_path, REQUIRED_COLUMNS[ImportType.players])
            return self.importer.import_players(db, csv_path, dry_run=dry_run)
        if import_type == ImportType.races:
            self._validate_required_columns(csv_path, REQUIRED_COLUMNS[ImportType.races])
            return self.importer.import_races(db, csv_path, dry_run=dry_run)
        if import_type == ImportType.entries:
            self._validate_required_columns(csv_path, REQUIRED_COLUMNS[ImportType.entries])
            return self.importer.import_entries(db, csv_path, dry_run=dry_run)
        if import_type == ImportType.results:
            self._validate_required_columns(csv_path, REQUIRED_COLUMNS[ImportType.results])
            return self.importer.import_results(db, csv_path, dry_run=dry_run)
        raise ValueError("Unsupported import type")

    def _validate_required_columns(self, csv_path: Path, expected_columns: list[str]) -> None:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            header_line = handle.readline()
        if not header_line.strip():
            raise ValueError("CSV file is empty")
        actual_columns = [column.strip() for column in header_line.rstrip("\r\n").split(",")]
        expected = [column.strip() for column in expected_columns]
        if actual_columns != expected:
            raise ValueError(f"Invalid CSV header. Expected: {expected_columns}, got: {actual_columns}")

    def _create_dry_run_session(self, db: Session) -> tuple[Session, tuple[object | None, Path | None]]:
        bind = db.get_bind()
        if bind is None or getattr(bind, "url", None) is None:
            raise ValueError("Unable to create dry-run session")

        if bind.url.get_backend_name() == "sqlite":
            source_database = bind.url.database
            if source_database:
                source_path = Path(source_database)
                if not source_path.is_absolute():
                    source_path = Path.cwd() / source_path
                with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle:
                    temp_database = Path(handle.name)
                shutil.copy2(source_path, temp_database)
                engine = get_engine(f"sqlite:///{temp_database.as_posix()}")
                session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
                return session, engine, temp_database

        connection = bind.connect()
        session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
        return session, connection, None

    def _cleanup_dry_run_resource(self, resource: object) -> None:
        if hasattr(resource, "rollback"):
            resource.rollback()  # type: ignore[call-arg]
        if hasattr(resource, "close"):
            resource.close()  # type: ignore[call-arg]
        if hasattr(resource, "dispose"):
            resource.dispose()  # type: ignore[call-arg]

    def _to_response(
        self,
        report: ImportReport,
        import_type: ImportType,
        filename: str,
        dry_run: bool,
    ) -> ImportResponseRead:
        errors = [
            ImportErrorRead(
                row_number=issue.row_number,
                error_code=self._map_error_code(issue),
                error_message=issue.error_message,
            )
            for issue in report.issues
        ]
        total = report.created + report.skipped + report.failed
        return ImportResponseRead(
            import_type=import_type,
            filename=filename,
            dry_run=dry_run,
            total=total,
            created=report.created,
            updated=0,
            skipped=report.skipped,
            failed=report.failed,
            errors=errors,
        )

    def _map_error_code(self, issue: ImportIssue) -> str:
        mapping = {
            "lookup_error": "LOOKUP_ERROR",
            "validation_error": "INVALID_VALUE",
            "unexpected_error": "INTERNAL_ERROR",
        }
        return mapping.get(issue.error_code, "INVALID_VALUE")
