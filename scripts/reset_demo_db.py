from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
SAMPLES_DIR = ROOT_DIR / "samples"
DEFAULT_DATABASE_URL = f"sqlite:///{BACKEND_DIR / 'kip.db'}"

sys.path.insert(0, str(BACKEND_DIR))

import app.models  # noqa: F401,E402
from app.db.session import get_engine, get_session_factory  # noqa: E402
from app.api.v1.tracks.router import list_tracks  # noqa: E402
from app.services.imports.race_data import CSVImportService  # noqa: E402


@dataclass(frozen=True)
class DemoDbSummary:
    database_path: Path
    alembic_revision: str
    tracks: int
    players: int
    races: int
    entries: int
    results: int
    foreign_key_validation: bool
    api_readable: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reset the local KIP demo database.")
    parser.add_argument("--dry-run", action="store_true", help="Show planned steps without changing files.")
    parser.add_argument("--no-backup", action="store_true", help="Reset without creating a backup copy.")
    return parser


def resolve_database_url() -> str:
    return os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL


def is_sqlite_url(database_url: str) -> bool:
    return database_url.startswith("sqlite:///")


def database_path_from_url(database_url: str) -> Path:
    if not is_sqlite_url(database_url):
        raise ValueError("reset_demo_db.py supports SQLite demo databases only.")
    raw_path = database_url.removeprefix("sqlite:///")
    return Path(raw_path)


def ensure_unique_backup_path(backups_dir: Path, source_path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backups_dir / f"{source_path.stem}_{timestamp}{source_path.suffix}"
    counter = 2
    while backup_path.exists():
        backup_path = backups_dir / f"{source_path.stem}_{timestamp}_{counter}{source_path.suffix}"
        counter += 1
    return backup_path


def backup_database(source_path: Path, backups_dir: Path) -> Path | None:
    if not source_path.exists():
        return None
    backups_dir.mkdir(parents=True, exist_ok=True)
    backup_path = ensure_unique_backup_path(backups_dir, source_path)
    shutil.copy2(source_path, backup_path)
    if not backup_path.exists() or backup_path.stat().st_size == 0:
        raise RuntimeError("Database backup failed.")
    return backup_path


def run_alembic(database_url: str, *args: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        check=True,
    )


def import_sample_data(database_url: str) -> None:
    session_factory = get_session_factory(database_url)
    importer = CSVImportService()
    with session_factory() as db:
        import_order = [
            ("tracks", SAMPLES_DIR / "tracks.csv"),
            ("players", SAMPLES_DIR / "players.csv"),
            ("races", SAMPLES_DIR / "races.csv"),
            ("entries", SAMPLES_DIR / "entries.csv"),
            ("results", SAMPLES_DIR / "results.csv"),
        ]
        for entity, csv_path in import_order:
            if entity == "tracks":
                report = importer.import_tracks(db, csv_path)
            elif entity == "players":
                report = importer.import_players(db, csv_path)
            elif entity == "races":
                report = importer.import_races(db, csv_path)
            elif entity == "entries":
                report = importer.import_entries(db, csv_path)
            else:
                report = importer.import_results(db, csv_path)
            if report.failed:
                raise RuntimeError(f"{entity} import failed: {', '.join(report.errors)}")
        db.commit()


def validate_demo_database(database_url: str) -> DemoDbSummary:
    engine = get_engine(database_url)
    try:
        with engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            tracks = connection.execute(text("SELECT COUNT(*) FROM tracks")).scalar_one()
            players = connection.execute(text("SELECT COUNT(*) FROM players")).scalar_one()
            races = connection.execute(text("SELECT COUNT(*) FROM races")).scalar_one()
            entries = connection.execute(text("SELECT COUNT(*) FROM entries")).scalar_one()
            results = connection.execute(text("SELECT COUNT(*) FROM results")).scalar_one()
            fk_violations = connection.execute(text("PRAGMA foreign_key_check")).fetchall()

        api_readable = False
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = session_factory()
        try:
            tracks_payload = list_tracks(db=db)
            api_readable = isinstance(tracks_payload, list)
        finally:
            db.close()

        return DemoDbSummary(
            database_path=database_path_from_url(database_url),
            alembic_revision=revision,
            tracks=int(tracks),
            players=int(players),
            races=int(races),
            entries=int(entries),
            results=int(results),
            foreign_key_validation=(len(fk_violations) == 0),
            api_readable=api_readable,
        )
    finally:
        engine.dispose()


def reset_demo_database(*, dry_run: bool = False, no_backup: bool = False) -> DemoDbSummary | None:
    database_url = resolve_database_url()
    if not is_sqlite_url(database_url):
        raise ValueError("Reset demo DB is only intended for SQLite demo databases.")

    database_path = database_path_from_url(database_url)
    backups_dir = BACKEND_DIR / "backups"

    if dry_run:
        print(f"Planned database: {database_path}")
        print("Planned steps:")
        print("- Backup existing database" if database_path.exists() and not no_backup else "- No backup")
        print("- Remove existing database if present")
        print("- Run alembic upgrade head")
        print("- Import sample CSV files: tracks, players, races, entries, results")
        print("- Validate counts, foreign keys, and API readability")
        return None

    if database_path.exists():
        if no_backup:
            print("WARNING: --no-backup was used. Existing database will be replaced without a backup.")
        else:
            backup_path = backup_database(database_path, backups_dir)
            if backup_path is None:
                print("No existing database found. Skipping backup.")
            else:
                print(f"Backed up existing database to {backup_path}")
        database_path.unlink()

    run_alembic(database_url, "upgrade", "head")
    import_sample_data(database_url)
    summary = validate_demo_database(database_url)
    if not summary.foreign_key_validation:
        raise RuntimeError("Foreign key validation failed.")
    if not summary.api_readable:
        raise RuntimeError("API application could not read the database.")
    return summary


def main() -> int:
    args = build_parser().parse_args()
    summary = reset_demo_database(dry_run=args.dry_run, no_backup=args.no_backup)
    if summary is None:
        return 0

    revision_short = summary.alembic_revision.split("_", 1)[0]
    print(f"Database: {summary.database_path}")
    print(f"Alembic revision: {revision_short}")
    print(f"Tracks: {summary.tracks}")
    print(f"Players: {summary.players}")
    print(f"Races: {summary.races}")
    print(f"Entries: {summary.entries}")
    print(f"Results: {summary.results}")
    print(f"Foreign key validation: {'PASS' if summary.foreign_key_validation else 'FAIL'}")
    print(f"API readable: {'PASS' if summary.api_readable else 'FAIL'}")
    print("Demo database status: READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
