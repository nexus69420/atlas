"""SQLAlchemy declarative base for all ORM models.

Every model should inherit from `Base` so Alembic can discover
metadata in one place when we add migrations later.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for Atlas ORM models."""
