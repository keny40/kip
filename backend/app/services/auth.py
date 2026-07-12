from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.users import User
from app.services.users import UserService


class AuthService:
    def __init__(self, user_service: UserService | None = None) -> None:
        self.user_service = user_service or UserService()

    def authenticate_user(self, db: Session, email: str, password: str) -> User | None:
        user = self.user_service.get_by_email(db, email)
        if user is None:
            return None
        if user.status != "active" or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
