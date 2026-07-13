from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

from app.collectors.data_go_player_stats import (  # noqa: E402
    DataGoPlayerStatCollector,
    DataGoPlayerStatCollectorError,
    DataGoPlayerStatQuery,
)
from app.db.session import get_session_factory  # noqa: E402
from app.services.external_player_stat_import import (  # noqa: E402
    ExternalPlayerStatisticImportService,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect a small data.go player statistics preview.")
    parser.add_argument("--year", required=True, help="Standard year filter")
    parser.add_argument("--period-number", default=None, help="Optional rider generation filter")
    parser.add_argument("--name", default=None, help="Optional exact API name filter")
    parser.add_argument("--page-size", type=int, default=10, help="Rows per request, maximum 10")
    parser.add_argument("--max-pages", type=int, default=1, help="Maximum pages, must be 1")
    parser.add_argument("--database-url", required=True, help="Explicit staging database URL")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--inspect", action="store_true")
    return parser


def _mask_name(value: str) -> str:
    return "*" if len(value) <= 1 else value[0] + "*" * (len(value) - 1)


def _mask_period(value: str | None) -> str:
    if not value:
        return "unknown"
    return value[:1] + "*" * max(1, len(value) - 1)


def main() -> int:
    args = build_parser().parse_args()
    service_key = os.environ.get("DATA_GO_KR_SERVICE_KEY")
    if not service_key:
        print("COLLECTION_FAILED: DATA_GO_KR_SERVICE_KEY is not set.")
        return 1

    try:
        with DataGoPlayerStatCollector() as collector:
            collection = collector.collect(
                DataGoPlayerStatQuery(
                    service_key=service_key,
                    standard_year=args.year,
                    period_number=args.period_number,
                    racer_name=args.name,
                    page_size=args.page_size,
                    max_pages=args.max_pages,
                )
            )
    except DataGoPlayerStatCollectorError as exc:
        print(f"COLLECTION_FAILED: {exc}")
        return 1

    session_factory = get_session_factory(args.database_url)
    try:
        with session_factory() as db:
            report = ExternalPlayerStatisticImportService().upsert(
                db,
                collection.rows,
                dry_run=args.dry_run,
            )
            if args.apply:
                db.commit()
            else:
                db.rollback()
    except Exception:
        print("IMPORT_FAILED: Database operation failed.")
        return 1

    if args.inspect:
        required_missing = sum(
            issue.error_code in {"MISSING_STANDARD_YEAR", "MISSING_PLAYER_NAME"}
            for issue in collection.issues
        )
        print(f"API success: {collection.http_success}")
        print(f"Item count: {collection.item_count}")
        print(f"Normalization success: {len(collection.rows)}")
        print(f"Missing required values: {required_missing}")
        print(f"Provisional duplicate rows: {collection.duplicates_skipped}")
        print(f"Statistic parse errors: {collection.parse_error_count}")
        for row in collection.rows[:10]:
            print(
                f"name={_mask_name(row.racer_name)} "
                f"period_number={_mask_period(row.period_number)} "
                f"standard_year={row.standard_year} grade={row.grade}"
            )
    print(
        f"Import result: created={report.created} updated={report.updated} "
        f"skipped={report.skipped} failed={len(collection.issues)} dry_run={args.dry_run}"
    )
    for issue in collection.issues[:10]:
        print(
            f"error_code={issue.error_code} page={issue.page} row={issue.row} "
            f"message={issue.message}"
        )
    return 1 if collection.issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
