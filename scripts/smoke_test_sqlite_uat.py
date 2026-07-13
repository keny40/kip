from __future__ import annotations

import secrets
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
UAT_DB = (BACKEND / "kip_uat.db").resolve()
sys.path.insert(0, str(BACKEND))

from app.core.security import get_password_hash  # noqa: E402
from app.db.session import get_db, get_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.external_player_statistics import ExternalPlayerStatistic  # noqa: E402
from app.models.external_players import ExternalPlayer  # noqa: E402
from app.models.players import Player  # noqa: E402
from app.models.races import Race  # noqa: E402
from app.models.tracks import Track  # noqa: E402
from app.models.users import User  # noqa: E402


def require(client: TestClient, method: str, path: str, expected: int, **kwargs):
    response = client.request(method, path, **kwargs)
    if response.status_code != expected:
        raise RuntimeError(
            f"{method} {path}: expected {expected}, got {response.status_code}"
        )
    return response.json() if response.content else None


def run() -> None:
    if not UAT_DB.exists():
        raise RuntimeError("backend/kip_uat.db does not exist; prepare the UAT copy first.")

    with TemporaryDirectory(prefix="kip-sqlite-uat-smoke-") as temp_dir:
        smoke_db = Path(temp_dir) / "kip_uat_smoke.db"
        shutil.copy2(UAT_DB, smoke_db)
        database_url = f"sqlite:///{smoke_db.as_posix()}"
        engine = get_engine(database_url)
        session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

        suffix = secrets.token_hex(8)
        admin_email = f"uat-smoke-admin-{suffix}@example.invalid"
        viewer_email = f"uat-smoke-viewer-{suffix}@example.invalid"
        admin_password = secrets.token_urlsafe(36)
        viewer_password = secrets.token_urlsafe(36)
        with session_factory() as db:
            db.add_all(
                [
                    User(
                        email=admin_email,
                        username=f"uat-smoke-admin-{suffix}",
                        password_hash=get_password_hash(admin_password),
                        role="admin",
                        status="active",
                        is_active=True,
                    ),
                    User(
                        email=viewer_email,
                        username=f"uat-smoke-viewer-{suffix}",
                        password_hash=get_password_hash(viewer_password),
                        role="user",
                        status="active",
                        is_active=True,
                    ),
                ]
            )
            db.commit()
            race_id = db.scalar(select(Race.id).order_by(Race.id).limit(1))
            player_id = db.scalar(select(Player.id).order_by(Player.id).limit(1))
            expected_counts = {
                "players_count": db.scalar(select(func.count()).select_from(Player)),
                "external_players_count": db.scalar(
                    select(func.count()).select_from(ExternalPlayer)
                ),
                "external_player_statistics_count": db.scalar(
                    select(func.count()).select_from(ExternalPlayerStatistic)
                ),
            }
        if race_id is None or player_id is None:
            raise RuntimeError("UAT copy must contain at least one race and player.")

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
                require(client, "GET", path, 200)

            require(
                client,
                "POST",
                "/api/v1/auth/login",
                401,
                json={"email": admin_email, "password": "wrong"},
            )
            admin_token = require(
                client,
                "POST",
                "/api/v1/auth/login",
                200,
                json={"email": admin_email, "password": admin_password},
            )["access_token"]
            viewer_token = require(
                client,
                "POST",
                "/api/v1/auth/login",
                200,
                json={"email": viewer_email, "password": viewer_password},
            )["access_token"]
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

            require(client, "GET", "/api/v1/admin/external-players", 401)
            require(
                client,
                "GET",
                "/api/v1/admin/external-players",
                401,
                headers={"Authorization": "Bearer invalid-uat-token"},
            )
            require(
                client,
                "GET",
                "/api/v1/admin/data-quality-summary",
                403,
                headers=viewer_headers,
            )
            for path in [
                "/api/v1/admin/external-players",
                "/api/v1/admin/external-player-statistics",
                "/api/v1/admin/player-match-candidates",
                "/api/v1/admin/data-quality-summary",
            ]:
                require(client, "GET", path, 200, headers=admin_headers)

            summary = require(
                client,
                "GET",
                "/api/v1/admin/data-quality-summary?year=2025",
                200,
                headers=admin_headers,
            )
            if summary["counts"] != expected_counts:
                raise RuntimeError("UAT data-quality counts do not match the copied DB.")
            empty = require(
                client,
                "GET",
                "/api/v1/admin/external-players?name=__NO_SUCH_UAT_PLAYER__",
                200,
                headers=admin_headers,
            )
            if empty["meta"]["total"] != 0:
                raise RuntimeError("Invalid filter did not produce an empty result.")

            require(
                client,
                "GET",
                "/api/v1/admin/external-players/999999999",
                404,
                headers=admin_headers,
            )
            require(
                client,
                "POST",
                "/api/v1/admin/external-players",
                405,
                headers=admin_headers,
            )
            require(
                client,
                "POST",
                "/api/v1/admin/external-player-statistics",
                405,
                headers=admin_headers,
            )

            with session_factory() as db:
                before_players = db.scalar(select(func.count()).select_from(Player))
            player_csv = (ROOT / "samples" / "players.csv").read_bytes()
            report = require(
                client,
                "POST",
                "/api/v1/admin/imports/players?dry_run=true",
                200,
                headers=admin_headers,
                files={"file": ("players.csv", player_csv, "text/csv")},
            )
            with session_factory() as db:
                after_players = db.scalar(select(func.count()).select_from(Player))
            if before_players != after_players or report["failed"]:
                raise RuntimeError("CSV dry-run changed the smoke copy or reported failures.")

            print("SQLITE_UAT_SMOKE_OK")
            print("public_read=7 admin_read=4 auth_401_403=ok readonly_405=ok")
            print("not_found=404 empty_filter=ok csv_dry_run=ok source_db_unchanged=ok")
        finally:
            app.dependency_overrides.clear()
            client.close()
            engine.dispose()


if __name__ == "__main__":
    run()
