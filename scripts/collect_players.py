from __future__ import annotations

import argparse
import csv
import os
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy.orm import sessionmaker

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

from app.collectors.data_go import (  # noqa: E402
    DataGoCollectorError,
    DataGoKeirinPlayerCollector,
    DataGoQuery,
    export_players_csv,
    collect_players_to_csv,
    import_players_csv,
)
from app.db.session import get_engine  # noqa: E402
from app.db.session import get_session_factory  # noqa: E402
from app.services.imports.race_data import ImportReport  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect Keirin player data from data.go.kr and import it into KIP.")
    parser.add_argument("--service-key", default=os.getenv("DATA_GO_KR_SERVICE_KEY"), help="data.go.kr service key")
    parser.add_argument("--database-url", default=None, help="Override the database URL.")
    parser.add_argument("--base-url", default=None, help="Override the OpenAPI endpoint URL.")
    parser.add_argument("--year", type=int, default=None, help="Optional competition year filter.")
    parser.add_argument("--name", dest="racer_nm", default=None, help="Optional player name filter.")
    parser.add_argument(
        "--period-number",
        dest="period_no",
        type=int,
        default=None,
        help="Optional rider generation number filter (data.go.kr period_no).",
    )
    parser.add_argument("--page-size", type=int, default=100, help="Rows per page.")
    parser.add_argument("--max-pages", type=int, default=None, help="Maximum page count to fetch.")
    parser.add_argument("--dry-run", action="store_true", help="Validate without changing the database.")
    parser.add_argument("--inspect", action="store_true", help="Print a safe normalization summary.")
    return parser


def _resolve_sqlite_path(database_url: str) -> Path | None:
    if not database_url.startswith("sqlite:///"):
        return None
    raw_path = database_url.removeprefix("sqlite:///")
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def import_players_safely(csv_path: Path, *, database_url: str, dry_run: bool) -> tuple[object, object | None]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        if next(reader, None) is None:
            return ImportReport(entity="players"), "NO_STABLE_PLAYER_IDENTIFIER"

    if dry_run:
        sqlite_path = _resolve_sqlite_path(database_url)
        if sqlite_path is not None and sqlite_path.exists():
            with TemporaryDirectory() as temp_dir:
                temp_db_path = Path(temp_dir) / sqlite_path.name
                shutil.copy2(sqlite_path, temp_db_path)
                engine = get_engine(f"sqlite:///{temp_db_path.as_posix()}")
                session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                try:
                    with session_factory() as db:
                        report = import_players_csv(db, csv_path, dry_run=False)
                finally:
                    engine.dispose()
                return report, None

    session_factory = get_session_factory(database_url)
    with session_factory() as db:
        report = import_players_csv(db, csv_path, dry_run=dry_run)
        if dry_run:
            db.rollback()
        else:
            db.commit()
    return report, None


def main() -> int:
    args = build_parser().parse_args()
    if not args.service_key:
        print("Missing service key. Pass --service-key or set DATA_GO_KR_SERVICE_KEY.")
        return 1

    backend_database_url = args.database_url or os.getenv("DATABASE_URL")
    default_database_url = f"sqlite:///{backend_root / 'kip.db'}"
    database_url = backend_database_url or default_database_url

    query = DataGoQuery(
        service_key=args.service_key,
        stnd_yr=args.year,
        racer_nm=args.racer_nm,
        period_no=args.period_no,
        page_size=args.page_size,
        max_pages=args.max_pages,
    )

    with TemporaryDirectory() as temp_dir:
        csv_path = Path(temp_dir) / "players.csv"
        base_url = args.base_url or os.getenv("DATA_GO_KR_PLAYER_INFO_URL")
        collector = DataGoKeirinPlayerCollector(base_url=base_url) if base_url else DataGoKeirinPlayerCollector()
        try:
            if args.inspect:
                collection = collector.collect_players(query, inspect=True)
                export_players_csv(csv_path, collection.rows)
            else:
                collection = collect_players_to_csv(csv_path, query, collector=collector)
        except DataGoCollectorError as exc:
            print(f"Collection failed: {exc}")
            return 1
        finally:
            collector.close()

        try:
            report, import_skip_reason = import_players_safely(
                csv_path,
                database_url=database_url,
                dry_run=args.dry_run,
            )
        except Exception as exc:
            print(f"Import failed: {exc}")
            return 1

    print(
        "Collected players: "
        f"{len(collection.rows)} unique / {collection.duplicates_skipped} duplicates skipped / "
        f"{len(collection.issues)} collection issues"
    )
    if args.inspect:
        missing_player_number = sum(issue.error_code == "MISSING_PLAYER_NUMBER" for issue in collection.issues)
        missing_player_name = sum(issue.error_code == "MISSING_PLAYER_NAME" for issue in collection.issues)
        print(f"Item count: {collection.item_count}")
        print(f"XML tags: {', '.join(collection.observed_tags) if collection.observed_tags else '(none)'}")
        print(f"Normalization success: {len(collection.rows)}")
        print(f"Missing required values: {len(collection.issues)}")
        print(f"MISSING_PLAYER_NUMBER: {missing_player_number}")
        print(f"MISSING_PLAYER_NAME: {missing_player_name}")
        print(f"Grade unknown: {sum(row.grade == 'unknown' for row in collection.rows)}")
        print(f"Region unknown: {sum(row.region == 'unknown' for row in collection.rows)}")
        print(f"Status unknown: {sum(row.status == 'unknown' for row in collection.rows)}")
        print(f"Duplicate count: {collection.duplicates_skipped}")
        print(f"Duplicate key: {collection.duplicate_key}")
        for index, row in enumerate(collection.normalized_preview[:10], start=1):
            print(
                f"{index}. player_number={row.player_number}, name={row.name}, "
                f"grade={row.grade}, region={row.region}, status={row.status}"
            )
    print(
        "Import report: "
        f"created={report.created}, skipped={report.skipped}, failed={report.failed}, dry_run={args.dry_run}"
    )
    if import_skip_reason:
        print(f"Import skipped: {import_skip_reason}")
    for issue in collection.issues:
        print(
            f"- collection issue code={issue.error_code} "
            f"page={issue.page_no} row={issue.row_number}: {issue.message}"
        )

    if report.failed > 0 or collection.issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
