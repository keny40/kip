from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

from app.core.security import create_access_token, get_password_hash  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db, get_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.external_player_statistics import ExternalPlayerStatistic  # noqa: E402
from app.models.external_players import ExternalPlayer  # noqa: E402
from app.models.players import Player  # noqa: E402
from app.models.users import User  # noqa: E402


class DataQualityApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = TemporaryDirectory()
        cls.engine = get_engine(f"sqlite:///{Path(cls.temp.name) / 'quality.db'}")
        cls.Session = sessionmaker(bind=cls.engine)

        def override_db():
            with cls.Session() as db:
                yield db

        app.dependency_overrides[get_db] = override_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()
        cls.temp.cleanup()

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        now = datetime.now(timezone.utc)
        with self.Session() as db:
            admin = User(email="admin@quality.test", username="quality-admin", password_hash=get_password_hash("password"), role="admin", status="active", is_active=True)
            user = User(email="user@quality.test", username="quality-user", password_hash=get_password_hash("password"), role="user", status="active", is_active=True)
            db.add_all([admin, user, Player(name="기존", player_number=1, grade="A1", region="서울", status="active")])
            db.flush()
            self.admin_headers = {"Authorization": f"Bearer {create_access_token(str(admin.id), role='admin')}"}
            self.user_headers = {"Authorization": f"Bearer {create_access_token(str(user.id), role='user')}"}
            db.add_all([
                self._external("00000001", "유일", "01", "A1", now),
                self._external("00000002", "복수", "02", "A1", now),
                self._external("00000003", "복수", "02", "A1", now),
                self._external("00000004", "불일치", "04", "B1", now, region="unknown"),
            ])
            db.add_all([
                self._stat("유일", "01", "A1", now),
                self._stat("없음", "03", "A1", now, run_count=None),
                self._stat("복수", "02", "A1", now),
                self._stat("기수없음", None, "unknown", now),
                self._stat("불일치", "04", "A1", now),
                self._stat("중복", "05", "A1", now),
                self._stat("중복", "05", "A1", now),
                self._stat("다른연도", "06", "A1", now, year="2024", source="other"),
            ])
            db.commit()

    def _external(self, external_id, name, period, grade, now, region="서울"):
        return ExternalPlayer(source="kcycle", external_id=external_id, name=name, period_number=period, grade=grade, region=region, status="unknown", collected_at=now)

    def _stat(self, name, period, grade, now, run_count=1, year="2025", source="data_go"):
        return ExternalPlayerStatistic(source=source, standard_year=year, racer_name=name, period_number=period, grade=grade, run_count=run_count, win_rate=None, high_rate=None, high_3_rate=None, collected_at=now)

    def test_auth_read_only_counts_quality_filters_and_invariance(self):
        self.assertEqual(self.client.get("/api/v1/admin/data-quality-summary").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/admin/data-quality-summary", headers=self.user_headers).status_code, 403)
        with self.Session() as db:
            before = (db.scalar(select(func.count()).select_from(Player)), db.scalar(select(func.count()).select_from(ExternalPlayer)), db.scalar(select(func.count()).select_from(ExternalPlayerStatistic)))
        response = self.client.get("/api/v1/admin/data-quality-summary?year=2025", headers=self.admin_headers)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["counts"], {"players_count": 1, "external_players_count": 4, "external_player_statistics_count": 7})
        self.assertEqual(body["statistics_quality"]["provisional_duplicate_count"], 1)
        self.assertEqual(body["statistics_quality"]["invalid_or_null_run_count"], 1)
        self.assertEqual(body["statistics_quality"]["unknown_grade_count"], 1)
        self.assertEqual(body["match_status_counts"], {"UNIQUE_CANDIDATE": 1, "NO_CANDIDATE": 3, "MULTIPLE_CANDIDATES": 1, "MISSING_PERIOD_NUMBER": 1, "GRADE_MISMATCH": 1})
        self.assertEqual(body["coverage"]["unique_candidate_rate"], 14.3)
        filtered = self.client.get("/api/v1/admin/data-quality-summary?source=other", headers=self.admin_headers).json()
        self.assertEqual(filtered["counts"]["external_players_count"], 0)
        self.assertEqual(filtered["counts"]["external_player_statistics_count"], 1)
        self.assertEqual(self.client.post("/api/v1/admin/data-quality-summary", headers=self.admin_headers).status_code, 405)
        with self.Session() as db:
            after = (db.scalar(select(func.count()).select_from(Player)), db.scalar(select(func.count()).select_from(ExternalPlayer)), db.scalar(select(func.count()).select_from(ExternalPlayerStatistic)))
        self.assertEqual(before, after)

    def test_zero_rows_has_zero_rate(self):
        body = self.client.get("/api/v1/admin/data-quality-summary?year=1900", headers=self.admin_headers).json()
        self.assertEqual(body["coverage"]["total_statistics"], 0)
        self.assertEqual(body["coverage"]["unique_candidate_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
