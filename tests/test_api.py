from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db, get_engine
from app.models.users import User
from app.main import app


class ApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tempdir = TemporaryDirectory()
        db_path = Path(cls._tempdir.name) / "test.db"
        cls.database_url = f"sqlite:///{db_path}"
        cls.engine = get_engine(cls.database_url)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        app.dependency_overrides.clear()
        cls.engine.dispose()
        cls._tempdir.cleanup()

    def setUp(self) -> None:
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        with self.SessionLocal() as db:
            admin = User(
                email="admin@example.com",
                username="admin",
                password_hash=get_password_hash("admin-password"),
                role="admin",
                status="active",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            self.admin_headers = {
                "Authorization": f"Bearer {create_access_token(str(admin.id), role=admin.role)}"
            }

    def create_track(
        self,
        *,
        code: str = "SEOUL",
        name: str = "Seoul Velodrome",
        region: str = "Seoul",
        address: str = "Seoul",
        status: str = "active",
    ) -> dict:
        response = self.client.post(
            "/api/v1/tracks",
            json={
                "code": code,
                "name": name,
                "region": region,
                "address": address,
                "status": status,
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def create_player(self, player_number: int = 101, name: str = "Player Alpha") -> dict:
        response = self.client.post(
            "/api/v1/players",
            json={
                "name": name,
                "player_number": player_number,
                "grade": "A1",
                "region": "Seoul",
                "status": "active",
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def create_race(
        self,
        *,
        race_date: str = "2026-07-12",
        track_code: str = "SEOUL",
        track_name: str = "Seoul Velodrome",
        race_number: int = 1,
        scheduled_start_time: str = "09:00:00",
        status: str = "scheduled",
    ) -> dict:
        track = self.create_track(code=track_code, name=track_name)
        response = self.client.post(
            "/api/v1/races",
            json={
                "race_date": race_date,
                "track_id": track["id"],
                "track_name": track_name,
                "race_number": race_number,
                "scheduled_start_time": scheduled_start_time,
                "status": status,
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def create_entry(
        self,
        *,
        race_id: int,
        player_id: int,
        entry_number: int = 1,
        lane_number: int = 1,
        lineup_position: int = 1,
        status: str = "confirmed",
    ) -> dict:
        response = self.client.post(
            "/api/v1/entries",
            json={
                "race_id": race_id,
                "player_id": player_id,
                "entry_number": entry_number,
                "lane_number": lane_number,
                "lineup_position": lineup_position,
                "status": status,
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def create_result(
        self,
        *,
        race_id: int,
        player_id: int,
        finish_position: int = 1,
        finish_time: str | None = "02:58.12",
        result_status: str = "finished",
        points: int | None = 10,
    ) -> dict:
        response = self.client.post(
            "/api/v1/results",
            json={
                "race_id": race_id,
                "player_id": player_id,
                "finish_position": finish_position,
                "finish_time": finish_time,
                "result_status": result_status,
                "points": points,
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def create_user(
        self,
        *,
        email: str,
        password: str,
        username: str,
        role: str = "user",
        status: str = "active",
        is_active: bool = True,
    ) -> User:
        with self.SessionLocal() as db:
            user = User(
                email=email,
                username=username,
                password_hash=get_password_hash(password),
                role=role,
                status=status,
                is_active=is_active,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

    def test_health_check(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_cors_allows_local_web_origin(self) -> None:
        response = self.client.options(
            "/health",
            headers={
                "Origin": "http://127.0.0.1:5001",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://127.0.0.1:5001")

    def test_create_track_success(self) -> None:
        track = self.create_track()
        self.assertEqual(track["code"], "SEOUL")
        self.assertEqual(track["name"], "Seoul Velodrome")

    def test_list_tracks(self) -> None:
        self.create_track()
        response = self.client.get("/api/v1/tracks")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_create_track_duplicate_fails(self) -> None:
        self.create_track()
        response = self.client.post(
            "/api/v1/tracks",
            json={
                "code": "SEOUL2",
                "name": "Seoul Velodrome",
                "region": "Seoul",
                "address": "Seoul",
                "status": "active",
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 409)

    def test_create_race_success(self) -> None:
        data = self.create_race()
        self.assertEqual(data["track_name"], "Seoul Velodrome")
        self.assertEqual(data["race_number"], 1)
        self.assertEqual(data["track_id"], 1)

    def test_create_race_duplicate_fails(self) -> None:
        self.create_race()
        response = self.client.post(
            "/api/v1/races",
            json={
                "race_date": "2026-07-12",
                "track_id": 1,
                "track_name": "Seoul Velodrome",
                "race_number": 1,
                "scheduled_start_time": "09:00:00",
                "status": "scheduled",
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 400)

    def test_list_races(self) -> None:
        self.create_race(race_date="2026-07-11", race_number=1)
        self.create_race(race_date="2026-07-12", track_code="BUSAN", track_name="Busan Velodrome", race_number=2)
        response = self.client.get("/api/v1/races")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["meta"]["total"], 2)
        self.assertEqual(payload["items"][0]["race_date"], "2026-07-12")

    def test_get_race_detail(self) -> None:
        race = self.create_race()
        player = self.create_player()
        self.create_entry(race_id=race["id"], player_id=player["id"])

        response = self.client.get(f"/api/v1/races/{race['id']}")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["id"], race["id"])
        self.assertEqual(payload["track_name"], "Seoul Velodrome")
        self.assertEqual(len(payload["entries"]), 1)
        self.assertEqual(payload["entries"][0]["player"]["player_number"], 101)

    def test_race_results_and_status_update(self) -> None:
        race = self.create_race()
        player = self.create_player()
        self.create_entry(race_id=race["id"], player_id=player["id"])
        result = self.create_result(race_id=race["id"], player_id=player["id"])
        self.assertEqual(result["finish_position"], 1)

        race_response = self.client.get(f"/api/v1/races/{race['id']}")
        self.assertEqual(race_response.status_code, 200)
        self.assertEqual(race_response.json()["status"], "completed")

        race_results_response = self.client.get(f"/api/v1/races/{race['id']}/results")
        self.assertEqual(race_results_response.status_code, 200)
        self.assertEqual(len(race_results_response.json()["results"]), 1)

    def test_create_result_duplicate_fails(self) -> None:
        race = self.create_race()
        player = self.create_player()
        self.create_entry(race_id=race["id"], player_id=player["id"])
        self.create_result(race_id=race["id"], player_id=player["id"])
        response = self.client.post(
            "/api/v1/results",
            json={
                "race_id": race["id"],
                "player_id": player["id"],
                "finish_position": 1,
                "finish_time": "02:58.20",
                "result_status": "finished",
                "points": 8,
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 400)

    def test_player_statistics_and_history(self) -> None:
        race = self.create_race()
        player = self.create_player()
        self.create_entry(race_id=race["id"], player_id=player["id"])
        self.create_result(race_id=race["id"], player_id=player["id"])

        stats_response = self.client.get(f"/api/v1/players/{player['id']}/statistics")
        self.assertEqual(stats_response.status_code, 200)
        self.assertEqual(stats_response.json()["statistics"]["total_races"], 1)
        self.assertEqual(stats_response.json()["statistics"]["first_place_count"], 1)

        history_response = self.client.get(f"/api/v1/players/{player['id']}/race-history")
        self.assertEqual(history_response.status_code, 200)
        self.assertEqual(len(history_response.json()["history"]), 1)

    def test_player_statistics_filters_by_track(self) -> None:
        first_race = self.create_race(track_code="SEOUL", track_name="Seoul Velodrome")
        second_race = self.create_race(
            race_date="2026-07-13",
            track_code="BUSAN",
            track_name="Busan Velodrome",
            race_number=1,
        )
        player = self.create_player()
        self.create_entry(race_id=first_race["id"], player_id=player["id"])
        self.create_entry(race_id=second_race["id"], player_id=player["id"], entry_number=2)
        self.create_result(race_id=first_race["id"], player_id=player["id"])
        self.create_result(race_id=second_race["id"], player_id=player["id"])

        response = self.client.get(
            f"/api/v1/players/{player['id']}/statistics",
            params={"track_id": second_race["track_id"], "last_n": 1},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["filters"]["track_id"], second_race["track_id"])
        self.assertEqual(payload["statistics"]["total_races"], 1)

    def test_track_analytics_summary(self) -> None:
        race = self.create_race()
        player = self.create_player()
        self.create_entry(race_id=race["id"], player_id=player["id"])
        self.create_result(race_id=race["id"], player_id=player["id"])

        response = self.client.get(f"/api/v1/analytics/tracks/{race['track_id']}/summary")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["track_id"], race["track_id"])
        self.assertEqual(payload["total_races"], 1)

    def test_get_missing_race_returns_404(self) -> None:
        response = self.client.get("/api/v1/races/9999")
        self.assertEqual(response.status_code, 404)

    def test_create_player_success(self) -> None:
        data = self.create_player(player_number=201, name="Player Beta")
        self.assertEqual(data["player_number"], 201)
        self.assertEqual(data["name"], "Player Beta")

    def test_create_player_duplicate_number_fails(self) -> None:
        self.create_player(player_number=202)
        response = self.client.post(
            "/api/v1/players",
            json={
                "name": "Duplicate",
                "player_number": 202,
                "grade": "B1",
                "region": "Busan",
                "status": "active",
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 400)

    def test_create_entry_success(self) -> None:
        race = self.create_race()
        player = self.create_player(player_number=203)
        response = self.client.post(
            "/api/v1/entries",
            json={
                "race_id": race["id"],
                "player_id": player["id"],
                "entry_number": 1,
                "lane_number": 2,
                "lineup_position": 1,
                "status": "confirmed",
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["entry_number"], 1)

    def test_create_entry_duplicate_number_fails(self) -> None:
        race = self.create_race()
        player_one = self.create_player(player_number=204, name="Player One")
        player_two = self.create_player(player_number=205, name="Player Two")
        self.assertEqual(
            self.client.post(
                "/api/v1/entries",
                json={
                    "race_id": race["id"],
                    "player_id": player_one["id"],
                    "entry_number": 1,
                    "lane_number": 1,
                    "lineup_position": 1,
                    "status": "confirmed",
                },
                headers=self.admin_headers,
            ).status_code,
            201,
        )
        response = self.client.post(
            "/api/v1/entries",
            json={
                "race_id": race["id"],
                "player_id": player_two["id"],
                "entry_number": 1,
                "lane_number": 2,
                "lineup_position": 2,
                "status": "confirmed",
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 400)

    def test_login_success(self) -> None:
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "admin-password"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("access_token", payload)
        self.assertEqual(payload["token_type"], "bearer")
        self.assertEqual(payload["expires_in"], 3600)

    def test_admin_password_is_hashed(self) -> None:
        with self.SessionLocal() as db:
            admin = db.query(User).filter(User.email == "admin@example.com").one()
            self.assertNotEqual(admin.password_hash, "admin-password")
            self.assertTrue(verify_password("admin-password", admin.password_hash))

    def test_login_wrong_password_fails(self) -> None:
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 401)

    def test_login_missing_email_fails(self) -> None:
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "missing@example.com", "password": "admin-password"},
        )
        self.assertEqual(response.status_code, 401)

    def test_login_inactive_user_fails(self) -> None:
        self.create_user(
            email="inactive@example.com",
            password="inactive-password",
            username="inactive",
            status="inactive",
            is_active=False,
        )
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "inactive-password"},
        )
        self.assertEqual(response.status_code, 401)

    def test_auth_me_success(self) -> None:
        response = self.client.get("/api/v1/auth/me", headers=self.admin_headers)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["email"], "admin@example.com")
        self.assertEqual(payload["role"], "admin")

    def test_missing_token_rejected(self) -> None:
        response = self.client.post(
            "/api/v1/tracks",
            json={
                "code": "INC",
                "name": "Incheon Velodrome",
                "region": "Incheon",
                "address": "Incheon",
                "status": "active",
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_invalid_token_rejected(self) -> None:
        response = self.client.post(
            "/api/v1/tracks",
            json={
                "code": "BAD",
                "name": "Bad Track",
                "region": "Seoul",
                "address": "Seoul",
                "status": "active",
            },
            headers={"Authorization": "Bearer invalid.token.value"},
        )
        self.assertEqual(response.status_code, 401)

    def test_expired_token_rejected(self) -> None:
        expired_token = create_access_token("1", role="admin", expires_minutes=-1)
        response = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        self.assertEqual(response.status_code, 401)

    def test_non_admin_cannot_create_track(self) -> None:
        user = self.create_user(
            email="user@example.com",
            password="user-password",
            username="user",
            role="user",
            status="active",
            is_active=True,
        )
        token = create_access_token(str(user.id), role=user.role)
        response = self.client.post(
            "/api/v1/tracks",
            json={
                "code": "USER",
                "name": "User Track",
                "region": "Seoul",
                "address": "Seoul",
                "status": "active",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_track(self) -> None:
        response = self.client.post(
            "/api/v1/tracks",
            json={
                "code": "ADMIN",
                "name": "Admin Track",
                "region": "Seoul",
                "address": "Seoul",
                "status": "active",
            },
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 201)


if __name__ == "__main__":
    unittest.main()
