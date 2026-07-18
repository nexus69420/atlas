"""Database engine and session management.

Why sync SQLAlchemy for V1:
- Simpler mental model while the platform is a modular monolith
- Alembic migrations are straightforward with sync engines
- FastAPI runs sync DB calls in a threadpool automatically
- We can move to async (asyncpg) later if latency profiling demands it

Repositories own queries. Routes/services receive a Session via DI.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # drop stale connections before use
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a DB session for a single request, then close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
