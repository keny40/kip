from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.collectors.race_history import (  # noqa: E402
    RaceHistoryCollectorError,
    RaceHistoryPreviewCollector,
    RaceHistoryQuery,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview official keirin race history sources without writing to DB.")
    parser.add_argument("--mode", choices=("lineup", "result", "joined-preview"), default="lineup")
    parser.add_argument("--date-from", required=True)
    parser.add_argument("--date-to", required=True)
    parser.add_argument("--max-races", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--inspect", action="store_true", default=False)
    parser.add_argument("--lineup-endpoint", default=None, help="Confirmed data.go lineup service endpoint URL.")
    parser.add_argument("--result-endpoint", default=None, help="Confirmed data.go result service endpoint URL.")
    parser.add_argument("--meet-name", default=None, help="data.go meet_nm filter, e.g. 광명.")
    parser.add_argument("--year", default=None, help="data.go stnd_yr filter.")
    parser.add_argument("--week-count", default=None, help="data.go week_tcnt filter.")
    parser.add_argument("--day-count", default=None, help="data.go day_tcnt filter for result API.")
    parser.add_argument("--race-number", default=None, help="data.go race_no filter for result API.")
    parser.add_argument("--output", default="tmp/race_history_preview.json")
    parser.add_argument("--report", default="tmp/race_history_validation_report.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.dry_run:
        print("error_code=DRY_RUN_REQUIRED")
        print("message=This preview collector does not write to DB; pass --dry-run explicitly.")
        return 2
    query = RaceHistoryQuery(
        date_from=date.fromisoformat(args.date_from),
        date_to=date.fromisoformat(args.date_to),
        mode=args.mode,
        max_races=min(args.max_races, 10),
        lineup_endpoint=args.lineup_endpoint or "https://apis.data.go.kr/B551014/SRVC_OD_API_CRA_RACE_ORGAN/TODZ_API_CRA_RACE_ORGAN_I",
        result_endpoint=args.result_endpoint or "https://apis.data.go.kr/B551014/SRVC_TODZ_CRA_RACE_RESULT/TODZ_API_CRA_RACE_RESULT",
        meet_name=args.meet_name,
        standard_year=args.year,
        week_count=args.week_count,
        day_count=args.day_count,
        race_number=args.race_number,
    )
    try:
        with RaceHistoryPreviewCollector() as collector:
            preview = collector.collect_preview(query)
    except RaceHistoryCollectorError as exc:
        print(f"error_code=COLLECTOR_ERROR")
        print(f"message={exc}")
        return 1
    payload = {
        "source": preview.source,
        "mode": args.mode,
        "live_called": preview.live_called,
        "races_seen": preview.races_seen,
        "lineup_item_count": preview.lineup_item_count,
        "lineup_race_count": preview.lineup_race_count,
        "selected_lineup_entry_count": preview.selected_lineup_entry_count,
        "lineup_pages_fetched": preview.lineup_pages_fetched,
        "selected_lineup_entry_numbers": preview.selected_lineup_entry_numbers,
        "result_item_count": preview.result_item_count,
        "result_entry_numbers": preview.result_entry_numbers,
        "invalid_rank_value_count": preview.invalid_rank_value_count,
        "normalized_result_count": preview.normalized_result_count,
        "matched_result_count": preview.matched_result_count,
        "unmatched_result_count": preview.unmatched_result_count,
        "player_mismatch_count": preview.player_mismatch_count,
        "result_coverage_type": preview.result_coverage_type,
        "observed_result_tags": preview.observed_result_tags,
        "available_lineup_keys": preview.available_lineup_keys,
        "identifier_status": preview.identifier_status,
        "issues": [issue.__dict__ for issue in preview.issues],
        "source_notes": preview.source_notes,
        "races": preview.races[:10],
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "live_called": preview.live_called,
                "lineup_item_count": preview.lineup_item_count,
                "lineup_race_count": preview.lineup_race_count,
                "selected_lineup_entry_count": preview.selected_lineup_entry_count,
                "lineup_pages_fetched": preview.lineup_pages_fetched,
                "result_item_count": preview.result_item_count,
                "invalid_rank_value_count": preview.invalid_rank_value_count,
                "normalized_result_count": preview.normalized_result_count,
                "matched_result_count": preview.matched_result_count,
                "unmatched_result_count": preview.unmatched_result_count,
                "player_mismatch_count": preview.player_mismatch_count,
                "result_coverage_type": preview.result_coverage_type,
                "issue_counts": _issue_counts(payload["issues"]),
                "identifier_status": preview.identifier_status,
                "db_write": False,
                "mode": args.mode,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"live_called={str(preview.live_called).lower()}")
    print(f"mode={args.mode}")
    print(f"races_seen={preview.races_seen}")
    print(f"lineup_item_count={preview.lineup_item_count}")
    print(f"lineup_race_count={preview.lineup_race_count}")
    print(f"selected_lineup_entry_count={preview.selected_lineup_entry_count}")
    print(f"lineup_pages_fetched={preview.lineup_pages_fetched}")
    print(f"selected_lineup_entry_numbers={','.join(preview.selected_lineup_entry_numbers[:20])}")
    print(f"result_item_count={preview.result_item_count}")
    print(f"result_entry_numbers={','.join(preview.result_entry_numbers[:20])}")
    print(f"invalid_rank_value_count={preview.invalid_rank_value_count}")
    print(f"normalized_result_count={preview.normalized_result_count}")
    print(f"matched_result_count={preview.matched_result_count}")
    print(f"unmatched_result_count={preview.unmatched_result_count}")
    print(f"player_mismatch_count={preview.player_mismatch_count}")
    print(f"result_coverage_type={preview.result_coverage_type}")
    print(f"issues={len(preview.issues)}")
    for issue in preview.issues[:10]:
        print(f"issue={issue.error_code} page={issue.page or '-'} row={issue.row or '-'}")
    if args.inspect:
        print(f"output={args.output}")
        print(f"report={args.report}")
        print("source=data.go.kr 출주표_GW / 경주결과_GW catalog and KCYCLE official race pages")
    return 0


def _issue_counts(issues: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for issue in issues:
        code = str(issue.get("error_code"))
        counts[code] = counts.get(code, 0) + 1
    return counts


if __name__ == "__main__":
    raise SystemExit(main())
