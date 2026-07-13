from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy.engine import make_url


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.db.session import session_scope  # noqa: E402
from app.core.security import get_password_hash, verify_password  # noqa: E402
from app.services.users import UserService  # noqa: E402


def main() -> int:
    database_url = os.environ.get("DATABASE_URL", "")
    email = os.environ.get("KIP_UAT_ADMIN_EMAIL", "").strip()
    password = os.environ.get("KIP_UAT_ADMIN_PASSWORD", "")
    if not database_url or not email or not password:
        print("UAT_ADMIN_FAILED: required environment variables are missing.")
        return 2

    url = make_url(database_url)
    database = url.database
    if url.get_backend_name() != "sqlite" or not database:
        print("UAT_ADMIN_FAILED: UAT requires a SQLite database URL.")
        return 2
    database_path = Path(database).resolve()
    expected_path = (BACKEND / "kip_uat.db").resolve()
    if database_path != expected_path or not database_path.exists():
        print("UAT_ADMIN_FAILED: DATABASE_URL must point to backend/kip_uat.db.")
        return 2

    service = UserService()
    with session_scope(database_url) as db:
        existing = service.get_by_email(db, email)
        if existing is not None:
            if existing.role != "admin" or not existing.is_active or existing.status != "active":
                print("UAT_ADMIN_FAILED: existing UAT account is not an active administrator.")
                return 1
            password_updated = 0
            if not verify_password(password, existing.password_hash):
                existing.password_hash = get_password_hash(password)
                db.add(existing)
                password_updated = 1
            print(f"UAT_ADMIN_READY created=0 password_updated={password_updated}")
            return 0
        service.create_user(
            db,
            email=email,
            password=password,
            role="admin",
            status="active",
            is_active=True,
        )
    print("UAT_ADMIN_READY created=1 password_updated=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
