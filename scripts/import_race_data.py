from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

from app.db.session import get_session_factory  # noqa: E402
from app.services.imports.race_data import CSVImportService  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import KIP race CSV data.")
    parser.add_argument("entity", choices=["tracks", "players", "races", "entries", "results"])
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Validate without committing changes.")
    parser.add_argument("--error-report", type=Path, default=None, help="Optional CSV error report path.")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Override the database URL. Defaults to the app environment configuration.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    default_database_url = f"sqlite:///{backend_root / 'kip.db'}"
    session_factory = get_session_factory(args.database_url or default_database_url)
    importer = CSVImportService()

    with session_factory() as db:
        try:
            if args.entity == "tracks":
                report = importer.import_tracks(db, args.csv_path, dry_run=args.dry_run)
            elif args.entity == "players":
                report = importer.import_players(db, args.csv_path, dry_run=args.dry_run)
            elif args.entity == "races":
                report = importer.import_races(db, args.csv_path, dry_run=args.dry_run)
            elif args.entity == "entries":
                report = importer.import_entries(db, args.csv_path, dry_run=args.dry_run)
            else:
                report = importer.import_results(db, args.csv_path, dry_run=args.dry_run)

            if args.dry_run:
                db.rollback()
            else:
                db.commit()
        except Exception as exc:
            db.rollback()
            print(f"Import failed: {exc}")
            return 1

    print(
        f"{report.entity}: created={report.created}, skipped={report.skipped}, failed={report.failed}"
    )
    for error in report.errors:
        print(f"- {error}")
    if args.error_report is not None:
        with args.error_report.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["row_number", "import_type", "raw_data", "error_code", "error_message"],
            )
            writer.writeheader()
            for issue in report.issues:
                writer.writerow(
                    {
                        "row_number": issue.row_number,
                        "import_type": issue.import_type,
                        "raw_data": issue.raw_data,
                        "error_code": issue.error_code,
                        "error_message": issue.error_message,
                    }
                )
    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
