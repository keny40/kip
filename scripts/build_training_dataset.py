from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import session_scope  # noqa: E402
from app.ml.dataset_builder import TrainingDatasetBuilder  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a leakage-safe KIP race-entry training dataset.")
    parser.add_argument("--database-url", required=True, help="SQLAlchemy database URL. Read-only usage is expected.")
    parser.add_argument("--output", default="tmp/training_dataset.csv", help="CSV output path.")
    parser.add_argument("--report", default="tmp/training_dataset_report.json", help="JSON report output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    builder = TrainingDatasetBuilder()
    with session_scope(args.database_url) as db:
        report = builder.write_dataset(db, Path(args.output), Path(args.report))
    readiness = report["readiness"]
    summary = readiness["summary"]
    print(f"rows={report['row_count']}")
    print(f"valid_training_rows={report['valid_training_rows']}")
    print(f"completed_races={summary['completed_races']}")
    print(f"missing_result_rows={summary['missing_result_rows']}")
    print(f"readiness_status={readiness['status']}")
    if readiness["status"] != "READY":
        print("reason=INSUFFICIENT_TRAINING_DATA")
    print(f"output={args.output}")
    print(f"report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
