from datetime import datetime, timedelta, timezone


def create_access_token(subject: str, expires_minutes: int = 30) -> str:
    """TODO: Replace with real JWT creation."""
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    return f"todo-jwt::{subject}::{int(expires_at.timestamp())}"
