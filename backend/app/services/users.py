from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.users import User
from app.repositories.users import UserRepository


class UserService:
    def __init__(self, repository: UserRepository | None = None) -> None:
        self.repository = repository or UserRepository()

    def get_by_id(self, db: Session, user_id: int) -> User | None:
        return self.repository.get_by_id(db, user_id)

    def get_by_email(self, db: Session, email: str) -> User | None:
        return self.repository.get_by_email(db, email)

    def create_user(
        self,
        db: Session,
        *,
        email: str,
        password: str,
        username: str | None = None,
        role: str = "user",
        status: str = "active",
        is_active: bool = True,
    ) -> User:
        if self.repository.get_by_email(db, email):
            raise ValueError("email already exists")

        normalized_username = username or self._build_unique_username(db, email)
        if self.repository.get_by_username(db, normalized_username):
            normalized_username = self._build_unique_username(db, normalized_username)

        user = User(
            email=email,
            username=normalized_username,
            password_hash=get_password_hash(password),
            role=role,
            status=status,
            is_active=is_active,
        )
        return self.repository.create(db, user)

    def _build_unique_username(self, db: Session, seed: str) -> str:
        base = seed.split("@", 1)[0].strip().lower() or "admin"
        candidate = base
        suffix = 2
        while self.repository.get_by_username(db, candidate):
            candidate = f"{base}{suffix}"
            suffix += 1
        return candidate
