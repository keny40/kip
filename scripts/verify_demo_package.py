from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "kip_demo.db"
REQUIRED = (
    "README_FIRST.txt",
    "VERSION",
    "start_demo.ps1",
    "start_demo.cmd",
    "stop_demo.ps1",
    "stop_demo.cmd",
    "backend/app/main.py",
    "backend/alembic.ini",
    "backend/requirements-demo.txt",
    "frontend/index.html",
    "scripts/serve_demo_frontend.py",
    "scripts/run_demo_backend.py",
    "scripts/create_demo_admin.py",
    "scripts/create_sqlite_demo_db.py",
    "data/kip_demo.db",
)


def main() -> int:
    missing = [item for item in REQUIRED if not (ROOT / item).exists()]
    if missing:
        print("VERIFY_FAILED: required package files are missing.")
        return 1
    forbidden = []
    for pattern in (".env", ".git", "*.map", "*.symbols"):
        forbidden.extend(ROOT.rglob(pattern))
    forbidden.extend(path for path in ROOT.rglob("kip.db") if path.resolve() != DB.resolve())
    if forbidden:
        print("VERIFY_FAILED: forbidden debug, secret, Git, or operating DB artifacts found.")
        return 1
    connection = sqlite3.connect(f"file:{DB.resolve().as_posix()}?mode=ro", uri=True)
    try:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "tracks",
                "players",
                "races",
                "external_players",
                "external_player_statistics",
                "users",
            )
        }
        fk_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
    finally:
        connection.close()
    if revision != "0006_external_player_statistics" or fk_errors:
        print("VERIFY_FAILED: database revision or foreign keys are invalid.")
        return 1
    print(
        "VERIFY_OK "
        f"revision={revision} "
        + " ".join(f"{key}={value}" for key, value in counts.items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
