from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

from app.core.security import create_access_token, get_password_hash  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db, get_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.external_race_history import ExternalRace, ExternalRaceEntry, ExternalRaceResult  # noqa: E402
from app.models.players import Player  # noqa: E402
from app.models.users import User  # noqa: E402
from app.services.race_history_analytics import RaceHistoryAnalyticsService  # noqa: E402
from app.services.race_history_import import RaceHistoryImportService  # noqa: E402


def preview_payload(result_rank: int = 1) -> dict:
    return {
        "races": [
            {
                "source": "data_go",
                "standard_year": "2025",
                "meet_name": "광명",
                "week_count": 1,
                "day_count": 1,
                "race_number": "1",
                "race_date": "2025-01-03",
                "status": "completed",
                "collected_at": "2026-07-14T00:00:00+00:00",
                "entries": [
                    {"entry_number": "1", "player_name": "가상선수A", "period_number": "28", "grade": "A1", "external_player_id": None},
                    {"entry_number": "2", "player_name": "가상선수B", "period_number": "29", "grade": "A2", "external_player_id": None},
                ],
                "results": [
                    {"entry_number": "1", "player_name": "가상선수A", "period_number": "28", "result_rank": result_rank, "result_status": "FINISHED"},
                    {"entry_number": "2", "player_name": "가상선수B", "period_number": "29", "result_rank": 2, "result_status": "FINISHED"},
                ],
            }
        ]
    }


class RaceHistoryStagingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = TemporaryDirectory()
        self.engine = get_engine(f"sqlite:///{Path(self.tempdir.name) / 'test.db'}")
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.engine.dispose()
        self.tempdir.cleanup()

    def test_import_dry_run_apply_skip_and_update_without_players_change(self) -> None:
        with self.SessionLocal() as db:
            db.add(Player(name="기존선수", player_number=1, grade="A1", region="서울", status="active"))
            db.commit()
            before_players = db.query(Player).count()
            dry = RaceHistoryImportService().import_preview(db, preview_payload(), dry_run=True)
            self.assertEqual(dry.races_created, 1)
            self.assertEqual(db.query(ExternalRace).count(), 0)

            first = RaceHistoryImportService().import_preview(db, preview_payload(), dry_run=False)
            db.commit()
            self.assertEqual(first.races_created, 1)
            self.assertEqual(first.entries_created, 2)
            self.assertEqual(first.results_created, 2)
            self.assertEqual(db.query(ExternalRace).count(), 1)

            second = RaceHistoryImportService().import_preview(db, preview_payload(), dry_run=False)
            db.commit()
            self.assertEqual(second.races_skipped, 1)
            self.assertEqual(second.entries_skipped, 2)
            self.assertEqual(second.results_skipped, 2)

            changed = RaceHistoryImportService().import_preview(db, preview_payload(result_rank=3), dry_run=False)
            db.commit()
            self.assertEqual(changed.results_updated, 1)
            self.assertEqual(db.query(ExternalRace).count(), 1)
            self.assertEqual(db.query(Player).count(), before_players)

    def test_import_skips_identical_preview_when_collected_at_is_missing(self) -> None:
        payload = preview_payload()
        del payload["races"][0]["collected_at"]
        with self.SessionLocal() as db:
            first = RaceHistoryImportService().import_preview(db, payload, dry_run=False)
            db.commit()
            self.assertEqual(first.races_created, 1)
            self.assertEqual(first.entries_created, 2)
            self.assertEqual(first.results_created, 2)

            second = RaceHistoryImportService().import_preview(db, payload, dry_run=False)
            db.commit()
            self.assertEqual(second.races_updated, 0)
            self.assertEqual(second.entries_updated, 0)
            self.assertEqual(second.results_updated, 0)
            self.assertEqual(second.races_skipped, 1)
            self.assertEqual(second.entries_skipped, 2)
            self.assertEqual(second.results_skipped, 2)
            self.assertEqual(db.query(ExternalRace).count(), 1)
            self.assertEqual(db.query(ExternalRaceEntry).count(), 2)
            self.assertEqual(db.query(ExternalRaceResult).count(), 2)

    def test_analytics_summary_players_tracks_and_quality(self) -> None:
        with self.SessionLocal() as db:
            RaceHistoryImportService().import_preview(db, preview_payload(), dry_run=False)
            db.commit()
            service = RaceHistoryAnalyticsService()
            summary = service.summary(db)
            players = service.players(db)
            tracks = service.tracks(db)
            quality = service.quality(db)
        self.assertEqual(summary["total_races"], 1)
        self.assertEqual(summary["total_entries"], 2)
        self.assertIsNone(summary["result_coverage_rate"])
        self.assertEqual(summary["result_coverage_type"], "top3_only")
        self.assertEqual(players[0]["total_starts"], 1)
        self.assertIsNone(players[0]["average_rank"])
        self.assertEqual(tracks[0]["meet_name"], "광명")
        self.assertEqual(quality["missing_results"], 0)

    def test_admin_quality_requires_auth_and_post_is_405(self) -> None:
        response = self.client.get("/api/v1/admin/race-history-data-quality")
        self.assertEqual(response.status_code, 401)
        post = self.client.post("/api/v1/admin/race-history-data-quality")
        self.assertEqual(post.status_code, 405)

    def test_history_api_returns_read_only_analytics(self) -> None:
        with self.SessionLocal() as db:
            admin = User(
                email="admin@example.com",
                username="admin",
                password_hash=get_password_hash("pw"),
                role="admin",
                status="active",
                is_active=True,
            )
            db.add(admin)
            RaceHistoryImportService().import_preview(db, preview_payload(), dry_run=False)
            db.commit()
            admin_id = admin.id
        summary = self.client.get("/api/v1/analytics/history/summary")
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.json()["total_races"], 1)
        headers = {"Authorization": f"Bearer {create_access_token(str(admin_id), role='admin')}"}
        quality = self.client.get("/api/v1/admin/race-history-data-quality", headers=headers)
        self.assertEqual(quality.status_code, 200)
        self.assertEqual(quality.json()["race_count"], 1)


if __name__ == "__main__":
    unittest.main()
