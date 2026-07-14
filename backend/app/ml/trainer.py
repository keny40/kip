from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.ml.dataset_builder import TrainingDatasetBuilder, TrainingReadiness


@dataclass(frozen=True)
class BaselineTrainingResult:
    status: str
    reason: str | None
    trained: bool
    readiness: dict[str, object]
    message: str


class BaselineRankModelTrainer:
    """Guarded baseline trainer.

    This class intentionally refuses to train on tiny or incomplete datasets.
    A real estimator should only be plugged in behind this readiness gate.
    """

    def __init__(self, dataset_builder: TrainingDatasetBuilder | None = None) -> None:
        self.dataset_builder = dataset_builder or TrainingDatasetBuilder()

    def train_if_ready(self, db: Session) -> BaselineTrainingResult:
        readiness: TrainingReadiness = self.dataset_builder.assess_readiness(db)
        if readiness.status != "READY":
            return BaselineTrainingResult(
                status=readiness.status,
                reason=readiness.reason,
                trained=False,
                readiness=asdict(readiness),
                message="Training stopped because the verified historical race dataset is too small or incomplete.",
            )
        return BaselineTrainingResult(
            status="READY_NOT_TRAINED",
            reason="BASELINE_ESTIMATOR_NOT_CONFIGURED",
            trained=False,
            readiness=asdict(readiness),
            message=(
                "Readiness gates passed at "
                + datetime.utcnow().isoformat(timespec="seconds")
                + "Z, but no estimator is configured in this MVP step."
            ),
        )


def chronological_split_indices(row_count: int, train_ratio: float = 0.70, validation_ratio: float = 0.15) -> dict[str, tuple[int, int]]:
    if row_count < 1:
        return {"train": (0, 0), "validation": (0, 0), "test": (0, 0)}
    train_end = int(row_count * train_ratio)
    validation_end = train_end + int(row_count * validation_ratio)
    train_end = max(0, min(train_end, row_count))
    validation_end = max(train_end, min(validation_end, row_count))
    return {
        "train": (0, train_end),
        "validation": (train_end, validation_end),
        "test": (validation_end, row_count),
    }
