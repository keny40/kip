from __future__ import annotations

import argparse
import sys
from getpass import getpass
from pathlib import Path

backend_root = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_root))

from app.db.session import session_scope
from app.services.users import UserService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create an admin account for the KIP demo database.")
    parser.add_argument("--email", required=True, help="Admin email address")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    password = getpass("Password: ")
    password_confirm = getpass("Confirm password: ")

    if not password:
        print("Password cannot be empty.", file=sys.stderr)
        return 1
    if password != password_confirm:
        print("Passwords do not match.", file=sys.stderr)
        return 1

    service = UserService()
    try:
        with session_scope() as db:
            user = service.create_user(
                db,
                email=args.email,
                password=password,
                role="admin",
                status="active",
                is_active=True,
            )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Admin user created: {user.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
