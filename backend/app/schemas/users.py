from datetime import datetime

from app.schemas.common import ORMModel


class UserRead(ORMModel):
    id: int
    email: str
    username: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime
