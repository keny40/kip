from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import session_scope  # noqa: E402
from app.services.race_history_import import RaceHistoryImportService  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import race history preview JSON into external race staging tables.")
    parser.add_argument("--file", required=True)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--inspect", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.dry_run == args.apply:
        print("error_code=MODE_REQUIRED")
        print("message=Choose exactly one of --dry-run or --apply.")
        return 2
    payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
    with session_scope(args.database_url) as db:
        report = RaceHistoryImportService().import_preview(db, payload, dry_run=args.dry_run)
    data = report.as_dict()
    for key, value in data.items():
        if key != "issues":
            print(f"{key}={value}")
    if args.inspect:
        print(f"issues={len(data['issues'])}")
    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
