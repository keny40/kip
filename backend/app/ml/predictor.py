from __future__ import annotations

from dataclasses import asdict

from sqlalchemy.orm import Session, joinedload

from app.ml.dataset_builder import TrainingDatasetBuilder
from app.models.races import Race


class RacePredictionService:
    def __init__(self, dataset_builder: TrainingDatasetBuilder | None = None) -> None:
        self.dataset_builder = dataset_builder or TrainingDatasetBuilder()

    def predict_race(self, db: Session, race_id: int) -> dict[str, object]:
        race = db.get(Race, race_id, options=[joinedload(Race.track), joinedload(Race.entries)])
        if race is None:
            raise LookupError("race not found")

        readiness = self.dataset_builder.assess_readiness(db)
        if readiness.status != "READY":
            return {
                "race_id": race.id,
                "race_date": race.race_date,
                "track_code": race.track.code if race.track else None,
                "race_number": race.race_number,
                "model_status": "not_ready",
                "reason": readiness.reason,
                "readiness": asdict(readiness),
                "predictions": [],
            }

        return {
            "race_id": race.id,
            "race_date": race.race_date,
            "track_code": race.track.code if race.track else None,
            "race_number": race.race_number,
            "model_status": "not_ready",
            "reason": "MODEL_NOT_READY",
            "readiness": asdict(readiness),
            "predictions": [],
        }
