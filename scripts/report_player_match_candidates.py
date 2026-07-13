from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path
import sys

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

from app.db.session import get_session_factory  # noqa: E402
from app.services.player_match_candidates import PlayerMatchCandidateService  # noqa: E402


REPORT_FIELDS = (
    "statistic_id",
    "standard_year",
    "masked_racer_name",
    "period_number",
    "statistic_grade",
    "candidate_count",
    "match_status",
    "masked_external_id",
    "external_grade",
    "grade_matches",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a read-only external player candidate report.")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--year", default=None)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--format", choices=("csv", "json"), default="csv")
    parser.add_argument("--output", type=Path, default=Path("tmp/player_match_candidates_preview.csv"))
    parser.add_argument("--inspect", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not 1 <= args.limit <= 1000:
        print("REPORT_FAILED: limit must be between 1 and 1000.")
        return 1
    session_factory = get_session_factory(args.database_url)
    try:
        with session_factory() as db:
            rows = PlayerMatchCandidateService().build_report(
                db,
                year=args.year,
                limit=args.limit,
            )
            db.rollback()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.format == "json":
            args.output.write_text(
                json.dumps([asdict(row) for row in rows], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        else:
            with args.output.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(REPORT_FIELDS))
                writer.writeheader()
                writer.writerows(asdict(row) for row in rows)
    except (OSError, ValueError) as exc:
        print(f"REPORT_FAILED: {exc}")
        return 1
    except Exception:
        print("REPORT_FAILED: Database operation failed.")
        return 1

    if args.inspect:
        counts: dict[str, int] = {}
        for row in rows:
            counts[row.match_status] = counts.get(row.match_status, 0) + 1
        print(f"Report rows: {len(rows)}")
        for status in sorted(counts):
            print(f"{status}: {counts[status]}")
    print(f"Report file: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
