from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select, text


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.security import get_password_hash  # noqa: E402
from app.db.session import session_scope  # noqa: E402
from app.models.external_player_statistics import ExternalPlayerStatistic  # noqa: E402
from app.models.external_players import ExternalPlayer  # noqa: E402
from app.models.users import User  # noqa: E402
from app.models.players import Player  # noqa: E402
from app.models.races import Race  # noqa: E402
from app.models.tracks import Track  # noqa: E402
from scripts.reset_demo_db import import_sample_data  # noqa: E402


def seed_phase2_data(
    database_url: str,
    *,
    admin_email: str,
    admin_username: str,
    admin_password: str,
) -> dict[str, int]:
    if not admin_password:
        raise ValueError("KIP_ADMIN_PASSWORD is required when demo seeding is enabled.")

    import_sample_data(database_url)
    now = datetime.now(timezone.utc)
    with session_scope(database_url) as db:
        revision = db.scalar(text("SELECT version_num FROM alembic_version"))
        if revision != "0006_external_player_statistics":
            raise RuntimeError("Database must be migrated to 0006 before Phase 2 seeding.")

        admin = db.scalar(select(User).where(User.email == admin_email))
        if admin is None:
            db.add(
                User(
                    email=admin_email,
                    username=admin_username,
                    password_hash=get_password_hash(admin_password),
                    role="admin",
                    status="active",
                    is_active=True,
                )
            )

        external = db.scalar(
            select(ExternalPlayer).where(
                ExternalPlayer.source == "kcycle",
                ExternalPlayer.external_id == "00123456",
            )
        )
        if external is None:
            db.add(
                ExternalPlayer(
                    source="kcycle",
                    external_id="00123456",
                    name="Kim Min-joon",
                    period_number="01",
                    grade="A1",
                    region="unknown",
                    status="active",
                    detail_url="https://www.kcycle.or.kr/racer/info/00123456",
                    source_updated_at=None,
                    collected_at=now,
                )
            )

        statistic = db.scalar(
            select(ExternalPlayerStatistic).where(
                ExternalPlayerStatistic.source == "data_go",
                ExternalPlayerStatistic.standard_year == "2026",
                ExternalPlayerStatistic.racer_name == "Kim Min-joon",
                ExternalPlayerStatistic.period_number == "01",
            )
        )
        if statistic is None:
            db.add(
                ExternalPlayerStatistic(
                    source="data_go",
                    standard_year="2026",
                    racer_name="Kim Min-joon",
                    period_number="01",
                    grade="A1",
                    run_count=1,
                    run_day_count=1,
                    rank1_count=1,
                    win_rate=Decimal("100.000"),
                    high_rate=Decimal("100.000"),
                    high_3_rate=Decimal("100.000"),
                    collected_at=now,
                )
            )

    with session_scope(database_url) as db:
        return {
            "tracks": int(db.scalar(select(func.count()).select_from(Track)) or 0),
            "players": int(db.scalar(select(func.count()).select_from(Player)) or 0),
            "races": int(db.scalar(select(func.count()).select_from(Race)) or 0),
            "external_players": int(db.scalar(select(func.count()).select_from(ExternalPlayer)) or 0),
            "statistics": int(db.scalar(select(func.count()).select_from(ExternalPlayerStatistic)) or 0),
            "admins": int(db.scalar(select(func.count()).select_from(User).where(User.role == "admin")) or 0),
        }


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("SEED_FAILED: DATABASE_URL is required.")
        return 2
    try:
        summary = seed_phase2_data(
            database_url,
            admin_email=os.environ.get("KIP_ADMIN_EMAIL", "admin@example.com"),
            admin_username=os.environ.get("KIP_ADMIN_USERNAME", "admin"),
            admin_password=os.environ.get("KIP_ADMIN_PASSWORD", ""),
        )
    except Exception:
        print("SEED_FAILED: database setup failed.")
        return 1
    print("Phase 2 demo seed ready: " + " ".join(f"{key}={value}" for key, value in summary.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
