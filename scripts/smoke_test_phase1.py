from __future__ import annotations

import sys
from datetime import date, datetime, time, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.security import get_password_hash  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db, get_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.entries import Entry  # noqa: E402
from app.models.external_player_statistics import ExternalPlayerStatistic  # noqa: E402
from app.models.external_players import ExternalPlayer  # noqa: E402
from app.models.players import Player  # noqa: E402
from app.models.races import Race  # noqa: E402
from app.models.results import Result  # noqa: E402
from app.models.tracks import Track  # noqa: E402
from app.models.users import User  # noqa: E402
from app.services.external_player_import import ExternalPlayerCSVImportService  # noqa: E402


def require_status(client: TestClient, method: str, path: str, expected: int, **kwargs) -> dict | list | None:
    response = client.request(method, path, **kwargs)
    if response.status_code != expected:
        raise RuntimeError(f"{method} {path}: expected {expected}, got {response.status_code}")
    return response.json() if response.content else None


def seed(session_factory) -> tuple[int, int]:
    now = datetime.now(timezone.utc)
    with session_factory() as db:
        admin = User(email="phase1-admin@example.invalid", username="phase1-admin", password_hash=get_password_hash("phase1-admin-password"), role="admin", status="active", is_active=True)
        viewer = User(email="phase1-viewer@example.invalid", username="phase1-viewer", password_hash=get_password_hash("phase1-viewer-password"), role="user", status="active", is_active=True)
        track = Track(code="SMOKE", name="Smoke Track", region="local", address=None, status="active")
        player = Player(name="Smoke Player", player_number=900001, grade="A1", region="local", status="active")
        db.add_all([admin, viewer, track, player])
        db.flush()
        race = Race(race_date=date(2026, 1, 1), track_id=track.id, race_number=1, scheduled_start_time=time(12, 0), status="completed")
        db.add(race)
        db.flush()
        db.add_all([
            Entry(race_id=race.id, player_id=player.id, entry_number=1, lane_number=1, lineup_position=1, status="confirmed"),
            Result(race_id=race.id, player_id=player.id, finish_position=1, finish_time="1:00", result_status="finished", points=10),
            ExternalPlayer(source="kcycle", external_id="00000001", name="Smoke Player", period_number="01", grade="A1", region="unknown", status="active", collected_at=now),
            ExternalPlayerStatistic(source="data_go", standard_year="2026", racer_name="Smoke Player", period_number="01", grade="A1", run_count=1, win_rate=100, high_rate=100, high_3_rate=100, collected_at=now),
        ])
        db.commit()
        return race.id, player.id


def run() -> None:
    with TemporaryDirectory(prefix="kip-phase1-smoke-") as temp_dir:
        database_url = f"sqlite:///{Path(temp_dir) / 'smoke.db'}"
        engine = get_engine(database_url)
        session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        Base.metadata.create_all(engine)
        race_id, player_id = seed(session_factory)

        def override_db():
            with session_factory() as db:
                yield db

        app.dependency_overrides[get_db] = override_db
        client = TestClient(app)
        try:
            for path in [
                "/health",
                "/api/v1/tracks",
                "/api/v1/players",
                "/api/v1/races",
                f"/api/v1/races/{race_id}",
                f"/api/v1/players/{player_id}",
                "/api/v1/analytics/races/summary",
            ]:
                require_status(client, "GET", path, 200)

            require_status(client, "POST", "/api/v1/auth/login", 401, json={"email": "phase1-admin@example.invalid", "password": "wrong"})
            token = require_status(client, "POST", "/api/v1/auth/login", 200, json={"email": "phase1-admin@example.invalid", "password": "phase1-admin-password"})["access_token"]
            viewer_token = require_status(client, "POST", "/api/v1/auth/login", 200, json={"email": "phase1-viewer@example.invalid", "password": "phase1-viewer-password"})["access_token"]
            admin_headers = {"Authorization": f"Bearer {token}"}
            viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

            require_status(client, "GET", "/api/v1/admin/external-players", 401)
            require_status(client, "GET", "/api/v1/admin/data-quality-summary", 403, headers=viewer_headers)
            for path in [
                "/api/v1/admin/external-players",
                "/api/v1/admin/external-player-statistics",
                "/api/v1/admin/player-match-candidates",
                "/api/v1/admin/data-quality-summary",
            ]:
                require_status(client, "GET", path, 200, headers=admin_headers)

            require_status(client, "POST", "/api/v1/players", 401, json={})
            require_status(client, "DELETE", f"/api/v1/tracks/1", 401)
            require_status(client, "POST", "/api/v1/admin/external-players", 405, headers=admin_headers)
            require_status(client, "POST", "/api/v1/admin/external-player-statistics", 405, headers=admin_headers)

            with session_factory() as db:
                before_players = db.scalar(select(func.count()).select_from(Player))
            player_csv = (ROOT / "samples" / "players.csv").read_bytes()
            player_report = require_status(
                client,
                "POST",
                "/api/v1/admin/imports/players?dry_run=true",
                200,
                headers=admin_headers,
                files={"file": ("players.csv", player_csv, "text/csv")},
            )
            with session_factory() as db:
                external_csv = Path(temp_dir) / "external.csv"
                external_csv.write_text(
                    "external_id,name,period_number,grade,region,status,detail_url,source,collected_at\n"
                    "00000002,Preview Player,02,A1,unknown,active,https://www.kcycle.or.kr/racer/info/00000002,kcycle,2026-01-01T00:00:00Z\n",
                    encoding="utf-8",
                )
                external_report = ExternalPlayerCSVImportService().import_csv(db, external_csv, dry_run=True)
                invalid_csv = Path(temp_dir) / "invalid-external.csv"
                invalid_csv.write_text(
                    "external_id,name,period_number,grade,region,status,detail_url,source,collected_at\n"
                    ",Missing Id,02,A1,unknown,active,,kcycle,2026-01-01T00:00:00Z\n",
                    encoding="utf-8",
                )
                invalid_report = ExternalPlayerCSVImportService().import_csv(db, invalid_csv, dry_run=True)
                after_players = db.scalar(select(func.count()).select_from(Player))
                if before_players != after_players or player_report["failed"] or external_report.failed or invalid_report.failed != 1:
                    raise RuntimeError(
                        "CSV dry-run invariance or validation failed: "
                        f"players={before_players}->{after_players}, "
                        f"player_failed={player_report['failed']}, "
                        f"external_failed={external_report.failed}, "
                        f"invalid_failed={invalid_report.failed}"
                    )

            print("PHASE1_SMOKE_OK")
            print("public_read=7 admin_read=4 auth_and_write_protection=ok")
            print(f"csv_dry_run=ok players_planned={player_report['created']} external_planned={external_report.created} invalid_failed={invalid_report.failed}")
        finally:
            app.dependency_overrides.clear()
            client.close()
            engine.dispose()


if __name__ == "__main__":
    run()
