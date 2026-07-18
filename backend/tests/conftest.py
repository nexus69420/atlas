"""Test fixtures — in-memory SQLite + temp storage root."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Import models so metadata is complete before create_all
from app.models import (  # noqa: F401
    Dataset,
    DatasetProfile,
    Deployment,
    Experiment,
    Explanation,
    Project,
    User,
)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(
    db_session: Session,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("STORAGE_PATH", str(tmp_path / "datasets"))
    monkeypatch.setenv("ARTIFACT_STORAGE_PATH", str(tmp_path / "artifacts"))
    get_settings.cache_clear()

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    """Register + login a default user; return Authorization headers."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@atlas.dev",
            "password": "securepass1",
            "full_name": "Project Owner",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@atlas.dev", "password": "securepass1"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def project_id(client: TestClient, auth_headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"name": "Data Workspace", "description": "For datasets"},
    )
    assert response.status_code == 201
    return response.json()["id"]
