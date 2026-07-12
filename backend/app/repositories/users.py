from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users import User


class UserRepository:
    def get_by_id(self, db: Session, user_id: int) -> User | None:
        return db.scalar(select(User).where(User.id == user_id))

    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email))

    def get_by_username(self, db: Session, username: str) -> User | None:
        return db.scalar(select(User).where(User.username == username))

    def create(self, db: Session, user: User) -> User:
        db.add(user)
        db.flush()
        db.refresh(user)
        return user
