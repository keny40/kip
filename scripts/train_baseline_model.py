from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import session_scope  # noqa: E402
from app.ml.trainer import BaselineRankModelTrainer  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the guarded baseline race-rank model only when data is sufficient.")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--metadata-output", default="artifacts/models/baseline_rank_model.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    trainer = BaselineRankModelTrainer()
    with session_scope(args.database_url) as db:
        result = trainer.train_if_ready(db)
    output_path = Path(args.metadata_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"status={result.status}")
    if result.reason:
        print(f"reason={result.reason}")
    print(f"trained={str(result.trained).lower()}")
    print(f"metadata={args.metadata_output}")
    return 2 if result.status == "INSUFFICIENT_TRAINING_DATA" else 0


if __name__ == "__main__":
    raise SystemExit(main())
