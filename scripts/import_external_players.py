from __future__ import annotations

import argparse
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

from app.db.session import get_session_factory  # noqa: E402
from app.services.external_player_import import ExternalPlayerCSVImportService  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate or import external player staging CSV data.")
    parser.add_argument("--file", type=Path, required=True, help="KCYCLE preview CSV file")
    parser.add_argument("--database-url", required=True, help="Explicit target database URL")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Plan changes without modifying the database")
    mode.add_argument("--apply", action="store_true", help="Apply staging table changes")
    parser.add_argument("--inspect", action="store_true", help="Print safe masked diagnostics")
    return parser


def _mask_external_id(value: str) -> str:
    return value[:4] + "*" * max(0, len(value) - 4)


def _mask_name(value: str) -> str:
    if len(value) <= 1:
        return "*"
    return value[0] + "*" * (len(value) - 1)


def main() -> int:
    args = build_parser().parse_args()
    if not args.file.is_file():
        print("IMPORT_FAILED: CSV file does not exist.")
        return 1

    session_factory = get_session_factory(args.database_url)
    service = ExternalPlayerCSVImportService()
    try:
        with session_factory() as db:
            report = service.import_csv(db, args.file, dry_run=args.dry_run)
            if args.apply:
                db.commit()
            else:
                db.rollback()
    except (OSError, ValueError) as exc:
        print(f"IMPORT_FAILED: {exc}")
        return 1
    except Exception:
        print("IMPORT_FAILED: Database operation failed.")
        return 1

    if args.inspect:
        print(f"CSV total rows: {report.total_rows}")
        print(f"Valid rows: {report.valid_rows}")
        print(f"Created: {report.created}")
        print(f"Updated: {report.updated}")
        print(f"Skipped: {report.skipped}")
        print(f"Failed: {report.failed}")
        print(f"Duplicate source/external_id rows: {report.duplicate_rows}")
        for item in report.preview[:10]:
            changed = ",".join(item.changed_fields) if item.changed_fields else "none"
            print(
                f"action={item.action} external_id={_mask_external_id(item.external_id)} "
                f"name={_mask_name(item.name)} changed_fields={changed}"
            )
        for issue in report.issues[:10]:
            print(
                f"error_code={issue.error_code} row={issue.row_number} "
                f"message={issue.message}"
            )

    print(
        f"Import result: created={report.created} updated={report.updated} "
        f"skipped={report.skipped} failed={report.failed} dry_run={args.dry_run}"
    )
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
