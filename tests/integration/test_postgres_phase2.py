from __future__ import annotations

import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import sessionmaker


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

from app.core.security import get_password_hash  # noqa: E402
from app.db.session import get_db, get_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.external_player_statistics import ExternalPlayerStatistic  # noqa: E402
from app.models.external_players import ExternalPlayer  # noqa: E402
from app.models.players import Player  # noqa: E402
from app.models.races import Race  # noqa: E402
from app.models.users import User  # noqa: E402
from scripts.seed_phase2_data import seed_phase2_data  # noqa: E402


DATABASE_URL = os.environ.get("POSTGRES_TEST_DATABASE_URL")
RESET_ALLOWED = os.environ.get("KIP_ALLOW_POSTGRES_TEST_RESET") == "1"

pytestmark = [
    pytest.mark.postgres_integration,
    pytest.mark.skipif(
        not DATABASE_URL or not RESET_ALLOWED,
        reason="Disposable PostgreSQL URL and KIP_ALLOW_POSTGRES_TEST_RESET=1 are required",
    ),
]


def _alembic(*args: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = DATABASE_URL or ""
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND,
        env=env,
        check=True,
    )


def _request(client: TestClient, method: str, path: str, status: int, **kwargs):
    response = client.request(method, path, **kwargs)
    assert response.status_code == status, f"{method} {path}: {response.status_code}"
    return response.json() if response.content else None


def test_postgres_migration_seed_types_and_api_smoke() -> None:
    assert DATABASE_URL is not None
    engine = get_engine(DATABASE_URL)
    assert engine.dialect.name == "postgresql"

    # This test is intentionally destructive and is gated by an explicit opt-in.
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

    _alembic("upgrade", "head")
    inspector = inspect(engine)
    required = {
        "users", "tracks", "players", "races", "entries", "results",
        "external_players", "external_player_statistics",
    }
    assert required.issubset(set(inspector.get_table_names()))
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0006_external_player_statistics"

    unique_names = {item["name"] for item in inspector.get_unique_constraints("external_players")}
    assert "uq_external_players_source_external_id" in unique_names
    external_indexes = {item["name"] for item in inspector.get_indexes("external_players")}
    assert {"ix_external_players_source", "ix_external_players_external_id"}.issubset(external_indexes)

    _alembic("downgrade", "0005_external_players")
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0005_external_players"
    _alembic("upgrade", "head")

    admin_password = "phase2-postgres-smoke-password"
    seed_phase2_data(
        DATABASE_URL,
        admin_email="phase2-admin@example.invalid",
        admin_username="phase2-admin",
        admin_password=admin_password,
    )

    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    with Session() as db:
        external = db.scalar(select(ExternalPlayer).where(ExternalPlayer.external_id == "00123456"))
        statistic = db.scalar(select(ExternalPlayerStatistic).where(ExternalPlayerStatistic.standard_year == "2026"))
        assert external is not None and statistic is not None
        assert external.external_id == "00123456"
        assert external.period_number == "01"
        assert statistic.standard_year == "2026"
        assert statistic.period_number == "01"
        assert statistic.win_rate == Decimal("100.000")
        assert external.id > 0 and statistic.id > 0
        assert external.created_at is not None and external.updated_at is not None
        assert external.collected_at.utcoffset() is not None

        admin = db.scalar(select(User).where(User.email == "phase2-admin@example.invalid"))
        assert admin is not None and admin.is_active is True
        viewer = User(
            email="phase2-viewer@example.invalid",
            username="phase2-viewer",
            password_hash=get_password_hash("phase2-viewer-password"),
            role="user",
            status="active",
            is_active=True,
        )
        db.add(viewer)
        db.commit()

        race_id = db.scalar(select(Race.id).order_by(Race.id))
        assert race_id is not None

    entry_foreign_keys = {tuple(item["constrained_columns"]): item for item in inspect(engine).get_foreign_keys("entries")}
    assert entry_foreign_keys[("race_id",)]["options"].get("ondelete") == "CASCADE"
    assert entry_foreign_keys[("player_id",)]["options"].get("ondelete") == "RESTRICT"

    def override_db():
        with Session() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    try:
        _request(client, "GET", "/health", 200)
        _request(client, "POST", "/api/v1/auth/login", 401, json={"email": "phase2-admin@example.invalid", "password": "wrong"})
        admin_token = _request(client, "POST", "/api/v1/auth/login", 200, json={"email": "phase2-admin@example.invalid", "password": admin_password})["access_token"]
        viewer_token = _request(client, "POST", "/api/v1/auth/login", 200, json={"email": "phase2-viewer@example.invalid", "password": "phase2-viewer-password"})["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

        for path in ["/api/v1/tracks", "/api/v1/players", "/api/v1/races", f"/api/v1/races/{race_id}"]:
            _request(client, "GET", path, 200)
        _request(client, "GET", "/api/v1/admin/external-players", 401)
        _request(client, "GET", "/api/v1/admin/data-quality-summary", 403, headers=viewer_headers)
        for path in [
            "/api/v1/admin/external-players",
            "/api/v1/admin/external-player-statistics",
            "/api/v1/admin/player-match-candidates",
            "/api/v1/admin/data-quality-summary",
        ]:
            _request(client, "GET", path, 200, headers=admin_headers)
        with Session() as db:
            players_before = len(db.scalars(select(Player)).all())
        dry_run = _request(
            client,
            "POST",
            "/api/v1/admin/imports/players?dry_run=true",
            200,
            headers=admin_headers,
            files={
                "file": (
                    "players.csv",
                    b"player_number,name,grade,region,status\n990001,Postgres Preview,A1,Local,active\n",
                    "text/csv",
                )
            },
        )
        assert dry_run["created"] == 1 and dry_run["dry_run"] is True
        with Session() as db:
            assert len(db.scalars(select(Player)).all()) == players_before
        _request(client, "POST", "/api/v1/admin/external-players", 405, headers=admin_headers)
        _request(client, "POST", "/api/v1/admin/external-player-statistics", 405, headers=admin_headers)
    finally:
        app.dependency_overrides.clear()
        client.close()
        engine.dispose()
