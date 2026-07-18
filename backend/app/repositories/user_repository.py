"""User persistence — SQL only, no auth business rules."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: UUID) -> User | None:
        return self._db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self._db.scalars(statement).first()

    def create(
        self,
        *,
        email: str,
        hashed_password: str,
        full_name: str | None,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
