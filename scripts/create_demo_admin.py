from __future__ import annotations

import argparse
import os
import sys
from getpass import getpass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DEMO_DB = ROOT / "data" / "kip_demo.db"
sys.path.insert(0, str(BACKEND))

from app.db.session import session_scope  # noqa: E402
from app.services.users import UserService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an administrator in the demo DB only.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password-env", default="")
    args = parser.parse_args()
    if not DEMO_DB.exists() or DEMO_DB.resolve().parent != (ROOT / "data").resolve():
        print("ADMIN_SETUP_FAILED: demo database is missing or unsafe.")
        return 2
    password = os.environ.get(args.password_env, "") if args.password_env else getpass("Password: ")
    confirm = password if args.password_env else getpass("Confirm password: ")
    if len(password) < 12 or password != confirm:
        print("ADMIN_SETUP_FAILED: password must match and contain at least 12 characters.")
        return 1
    url = f"sqlite:///{DEMO_DB.resolve().as_posix()}"
    service = UserService()
    with session_scope(url) as db:
        existing = service.get_by_email(db, args.email.strip())
        if existing is not None:
            if existing.role == "admin" and existing.is_active and existing.status == "active":
                print("ADMIN_READY created=0")
                return 0
            print("ADMIN_SETUP_FAILED: the email belongs to a non-admin or inactive account.")
            return 1
        service.create_user(
            db,
            email=args.email.strip(),
            password=password,
            role="admin",
            status="active",
            is_active=True,
        )
    print("ADMIN_READY created=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
