from pydantic import Field

from app.schemas.common import ORMModel
from app.schemas.users import UserRead


class LoginRequest(ORMModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class TokenResponse(ORMModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class CurrentUserResponse(UserRead):
    pass
