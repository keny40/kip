from __future__ import annotations

import argparse
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

from app.collectors.kcycle_players import (  # noqa: E402
    KcyclePlayerCollector,
    KcyclePlayerCollectorError,
    KcyclePlayerQuery,
    export_kcycle_players_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect a small KCYCLE player master preview.")
    parser.add_argument("--max-pages", type=int, default=1, help="Must be 1; KCYCLE has one unpaged list.")
    parser.add_argument("--page-size", type=int, default=10, help="Preview limit from 1 to 10 players.")
    parser.add_argument("--output", type=Path, default=Path("tmp/kcycle_players_preview.csv"))
    parser.add_argument("--dry-run", action="store_true", help="Required; no database writes are implemented.")
    parser.add_argument("--inspect", action="store_true", help="Print safe masked collection diagnostics.")
    return parser


def _mask_external_id(value: str) -> str:
    return value[:4] + "*" * max(0, len(value) - 4)


def _mask_name(value: str) -> str:
    if len(value) <= 1:
        return "*"
    return value[0] + "*" * (len(value) - 1)


def main() -> int:
    args = build_parser().parse_args()
    if not args.dry_run:
        print("DRY_RUN_REQUIRED: Pass --dry-run. This collector does not write to the database.")
        return 2

    try:
        with KcyclePlayerCollector() as collector:
            result = collector.collect(
                KcyclePlayerQuery(page_size=args.page_size, max_pages=args.max_pages)
            )
        export_kcycle_players_csv(args.output, result.rows)
    except KcyclePlayerCollectorError as exc:
        print(f"COLLECTION_FAILED: {exc}")
        return 1
    except OSError as exc:
        print(f"OUTPUT_FAILED: {exc}")
        return 1

    if args.inspect:
        missing_external_id = sum(issue.error_code == "MISSING_EXTERNAL_ID" for issue in result.issues)
        missing_player_name = sum(issue.error_code == "MISSING_PLAYER_NAME" for issue in result.issues)
        print(f"HTTP request success: {result.http_success}")
        print(f"Response card count: {result.total_cards}")
        print(f"Inspected card count: {result.cards_seen}")
        print(f"Normalization success: {len(result.rows)}")
        print(f"MISSING_EXTERNAL_ID: {missing_external_id}")
        print(f"MISSING_PLAYER_NAME: {missing_player_name}")
        print(f"Duplicate racerNo count: {result.duplicates_skipped}")
        for row in result.rows[:10]:
            print(
                f"external_id={_mask_external_id(row.external_id)} "
                f"name={_mask_name(row.name)} period_number={row.period_number} grade={row.grade}"
            )
    print(f"Preview rows: {len(result.rows)}")
    print(f"Preview file: {args.output}")
    for issue in result.issues:
        print(
            f"{issue.error_code}: page={issue.page} row={issue.row} "
            f"{issue.message}"
        )
    return 0 if result.rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
