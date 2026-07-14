from __future__ import annotations

from datetime import date, time
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

import sys

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

from app.collectors.race_history import RaceHistoryPreviewCollector, RaceHistoryQuery  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db, get_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.ml.dataset_builder import TrainingDatasetBuilder  # noqa: E402
from app.ml.trainer import BaselineRankModelTrainer, chronological_split_indices  # noqa: E402
from app.models.entries import Entry  # noqa: E402
from app.models.players import Player  # noqa: E402
from app.models.races import Race  # noqa: E402
from app.models.results import Result  # noqa: E402
from app.models.tracks import Track  # noqa: E402


class PredictionMvpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = TemporaryDirectory()
        self.engine = get_engine(f"sqlite:///{Path(self.tempdir.name) / 'test.db'}")
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.engine.dispose()
        self.tempdir.cleanup()

    def _seed_two_races(self, *, missing_second_result: bool = False) -> tuple[int, int]:
        with self.SessionLocal() as db:
            track = Track(code="SEOUL", name="서울 경륜장", region="서울", status="active")
            player = Player(name="가상선수", player_number=1001, grade="A1", region="서울", status="active")
            other = Player(name="다른선수", player_number=1002, grade="A2", region="부산", status="active")
            db.add_all([track, player, other])
            db.flush()
            race1 = Race(
                race_date=date(2026, 1, 1),
                track_id=track.id,
                race_number=1,
                scheduled_start_time=time(10, 0),
                status="completed",
            )
            race2 = Race(
                race_date=date(2026, 1, 2),
                track_id=track.id,
                race_number=1,
                scheduled_start_time=time(10, 0),
                status="completed",
            )
            db.add_all([race1, race2])
            db.flush()
            db.add_all(
                [
                    Entry(race_id=race1.id, player_id=player.id, entry_number=1, lane_number=1, lineup_position=1),
                    Entry(race_id=race1.id, player_id=other.id, entry_number=2, lane_number=2, lineup_position=2),
                    Entry(race_id=race2.id, player_id=player.id, entry_number=1, lane_number=1, lineup_position=1),
                ]
            )
            db.flush()
            db.add_all(
                [
                    Result(race_id=race1.id, player_id=player.id, finish_position=2, result_status="finished"),
                    Result(race_id=race1.id, player_id=other.id, finish_position=1, result_status="finished"),
                ]
            )
            if not missing_second_result:
                db.add(Result(race_id=race2.id, player_id=player.id, finish_position=1, result_status="finished"))
            db.commit()
            return race1.id, race2.id

    def test_dataset_is_one_row_per_entry_and_uses_only_prior_results(self) -> None:
        self._seed_two_races()
        with self.SessionLocal() as db:
            rows = TrainingDatasetBuilder().build_rows(db)
        self.assertEqual(len(rows), 3)
        first_player_row = rows[0]
        second_player_row = rows[2]
        self.assertFalse(first_player_row.has_prior_history)
        self.assertEqual(first_player_row.recent5_start_count, 0)
        self.assertIsNone(first_player_row.recent5_avg_rank)
        self.assertEqual(second_player_row.recent5_start_count, 1)
        self.assertEqual(second_player_row.recent5_avg_rank, 2.0)
        self.assertEqual(second_player_row.recent5_win_count, 0)
        self.assertEqual(second_player_row.recent5_top3_count, 1)
        self.assertEqual(second_player_row.days_since_last_race, 1)

    def test_missing_results_are_marked_and_no_fake_player_id_is_created(self) -> None:
        self._seed_two_races(missing_second_result=True)
        with self.SessionLocal() as db:
            rows = TrainingDatasetBuilder().build_rows(db)
            summary = TrainingDatasetBuilder().summarize(db)
        missing = [row for row in rows if row.missing_result]
        self.assertEqual(len(missing), 1)
        self.assertIsNone(missing[0].result_rank)
        self.assertIsNone(missing[0].period_number)
        self.assertEqual(missing[0].player_number, 1001)
        self.assertEqual(summary.missing_result_rows, 1)
        self.assertFalse(summary.stable_external_player_identifier)

    def test_readiness_and_training_refuse_tiny_dataset(self) -> None:
        self._seed_two_races()
        with self.SessionLocal() as db:
            readiness = TrainingDatasetBuilder().assess_readiness(db)
            training = BaselineRankModelTrainer().train_if_ready(db)
        self.assertEqual(readiness.status, "INSUFFICIENT_TRAINING_DATA")
        self.assertIn("completed_races", readiness.deficits)
        self.assertEqual(training.status, "INSUFFICIENT_TRAINING_DATA")
        self.assertFalse(training.trained)

    def test_chronological_split_is_date_order_compatible(self) -> None:
        self.assertEqual(
            chronological_split_indices(100),
            {"train": (0, 70), "validation": (70, 85), "test": (85, 100)},
        )

    def test_prediction_api_returns_not_ready_before_model(self) -> None:
        _, race2_id = self._seed_two_races()

        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
                db.commit()
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        response = client.get(f"/api/v1/analytics/races/{race2_id}/prediction")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["model_status"], "not_ready")
        self.assertEqual(payload["reason"], "INSUFFICIENT_TRAINING_DATA")
        self.assertEqual(payload["predictions"], [])

    def test_race_history_preview_without_service_key_does_not_call_live_api(self) -> None:
        old_key = os.environ.pop("DATA_GO_KR_SERVICE_KEY", None)
        try:
            preview = RaceHistoryPreviewCollector().collect_preview(
                RaceHistoryQuery(date_from=date(2025, 1, 1), date_to=date(2025, 1, 31), max_races=10)
            )
        finally:
            if old_key is not None:
                os.environ["DATA_GO_KR_SERVICE_KEY"] = old_key
        self.assertFalse(preview.live_called)
        self.assertEqual(preview.issues[0].error_code, "SERVICE_KEY_MISSING")


if __name__ == "__main__":
    unittest.main()
