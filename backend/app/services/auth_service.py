"""Authentication business logic.

Routes call this service. The service never writes raw SQL —
that stays in UserRepository. Password hashing stays in core.security.
"""

from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserLoginRequest, UserRegisterRequest


@dataclass(frozen=True)
class AuthTokens:
    access_token: str


class AuthService:
    def __init__(self, db: Session) -> None:
        self._users = UserRepository(db)

    def register(self, payload: UserRegisterRequest) -> User:
        email = payload.email.lower().strip()
        if self._users.get_by_email(email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

        return self._users.create(
            email=email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
        )

    def login(self, payload: UserLoginRequest) -> AuthTokens:
        email = payload.email.lower().strip()
        user = self._users.get_by_email(email)

        if user is None or not verify_password(payload.password, user.hashed_password):
            # Same message for both cases — avoid email enumeration
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        return AuthTokens(access_token=create_access_token(user.id))

    def get_user(self, user_id: UUID) -> User:
        user = self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return user
