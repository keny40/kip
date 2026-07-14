from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select, text


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DATA = ROOT / "data"
SAMPLES = ROOT / "samples"
DEMO_DB = DATA / "kip_demo.db"
sys.path.insert(0, str(BACKEND))

from app.db.session import get_engine, session_scope  # noqa: E402
from app.models.external_player_statistics import ExternalPlayerStatistic  # noqa: E402
from app.models.external_players import ExternalPlayer  # noqa: E402
from app.models.players import Player  # noqa: E402
from app.models.races import Race  # noqa: E402
from app.models.tracks import Track  # noqa: E402
from app.models.users import User  # noqa: E402
from app.services.imports.race_data import CSVImportService  # noqa: E402


def database_url() -> str:
    return f"sqlite:///{DEMO_DB.resolve().as_posix()}"


def assert_safe_path() -> None:
    if DEMO_DB.resolve().parent != DATA.resolve() or DEMO_DB.name != "kip_demo.db":
        raise RuntimeError("Unsafe demo database target.")
    operating = (ROOT / "backend" / "kip.db").resolve()
    if DEMO_DB.resolve() == operating:
        raise RuntimeError("The operating database cannot be used as the demo database.")


def backup_existing() -> str | None:
    if not DEMO_DB.exists():
        return None
    backups = DATA / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = backups / f"kip_demo_{stamp}.db"
    counter = 2
    while target.exists():
        target = backups / f"kip_demo_{stamp}_{counter}.db"
        counter += 1
    shutil.copy2(DEMO_DB, target)
    if target.stat().st_size != DEMO_DB.stat().st_size:
        raise RuntimeError("Demo database backup verification failed.")
    return target.name


def migrate(url: str) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = url
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND,
        env=env,
        check=True,
    )


def import_samples(url: str) -> None:
    importer = CSVImportService()
    with session_scope(url) as db:
        reports = [
            importer.import_tracks(db, SAMPLES / "tracks.csv"),
            importer.import_players(db, SAMPLES / "players.csv"),
            importer.import_races(db, SAMPLES / "races.csv"),
            importer.import_entries(db, SAMPLES / "entries.csv"),
            importer.import_results(db, SAMPLES / "results.csv"),
        ]
        if any(report.failed for report in reports):
            raise RuntimeError("Sample data import failed.")


def seed_staging(url: str) -> None:
    now = datetime.now(timezone.utc)
    names = ["김민준", "이현수", "박지호", "최우진", "정태양", "한승민", "윤재현", "임동현", "신민재", "서준기"]
    regions = ["서울", "부산", "서울", "인천", "대구", "광주", "대전", "서울", "부산", "울산"]
    with session_scope(url) as db:
        for index in range(1, 11):
            external_id = f"{index:08d}"
            name = names[index - 1]
            period = f"{index:02d}"
            grade = ("A1", "A2", "B1")[index % 3]
            db.add(
                ExternalPlayer(
                    source="kcycle",
                    external_id=external_id,
                    name=name,
                    period_number=period,
                    grade=grade,
                    region=regions[index - 1],
                    status="active",
                    detail_url=None,
                    source_updated_at=None,
                    collected_at=now,
                )
            )
            db.add(
                ExternalPlayerStatistic(
                    source="data_go",
                    standard_year="2025",
                    racer_name=name,
                    period_number=period,
                    grade=grade,
                    run_count=index,
                    run_day_count=index,
                    rank1_count=index % 3,
                    rank2_count=index % 4,
                    rank3_count=index % 5,
                    win_rate=Decimal("10.000"),
                    high_rate=Decimal("30.000"),
                    high_3_rate=Decimal("50.000"),
                    collected_at=now,
                )
            )


def validate(url: str) -> dict[str, int | str]:
    engine = get_engine(url)
    try:
        with engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            fk_errors = connection.execute(text("PRAGMA foreign_key_check")).fetchall()
        if revision != "0006_external_player_statistics" or fk_errors:
            raise RuntimeError("Demo database validation failed.")
        with session_scope(url) as db:
            counts: dict[str, int | str] = {
                "revision": revision,
                "tracks": int(db.scalar(select(func.count()).select_from(Track)) or 0),
                "players": int(db.scalar(select(func.count()).select_from(Player)) or 0),
                "races": int(db.scalar(select(func.count()).select_from(Race)) or 0),
                "external_players": int(
                    db.scalar(select(func.count()).select_from(ExternalPlayer)) or 0
                ),
                "statistics": int(
                    db.scalar(select(func.count()).select_from(ExternalPlayerStatistic)) or 0
                ),
                "users": int(db.scalar(select(func.count()).select_from(User)) or 0),
            }
        return counts
    finally:
        engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the isolated SQLite demo database.")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    assert_safe_path()
    DATA.mkdir(parents=True, exist_ok=True)
    if DEMO_DB.exists() and not args.replace:
        print("DEMO_DB_FAILED: database already exists; use the confirmed reset procedure.")
        return 2
    backup_name = backup_existing() if args.replace else None
    if DEMO_DB.exists():
        DEMO_DB.unlink()
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = Path(f"{DEMO_DB}{suffix}")
        if sidecar.exists():
            sidecar.unlink()
    url = database_url()
    migrate(url)
    import_samples(url)
    seed_staging(url)
    counts = validate(url)
    revision = str(counts.pop("revision"))
    print(f"DEMO_DB_READY revision={revision} " + " ".join(f"{k}={v}" for k, v in counts.items()))
    if backup_name:
        print(f"DEMO_DB_BACKUP_CREATED file={backup_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
