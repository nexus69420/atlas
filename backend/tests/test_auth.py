"""Auth API smoke tests (register → login → me)."""

from fastapi.testclient import TestClient


def test_register_login_me_flow(client: TestClient) -> None:
    register_payload = {
        "email": "engineer@atlas.dev",
        "password": "securepass1",
        "full_name": "Atlas Engineer",
    }

    register_response = client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201
    body = register_response.json()
    assert body["email"] == "engineer@atlas.dev"
    assert body["full_name"] == "Atlas Engineer"
    assert "hashed_password" not in body
    assert "id" in body

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "engineer@atlas.dev",
            "password": "securepass1",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    assert login_response.json()["token_type"] == "bearer"
    assert token

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "engineer@atlas.dev"


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    payload = {
        "email": "dup@atlas.dev",
        "password": "securepass1",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    conflict = client.post("/api/v1/auth/register", json=payload)
    assert conflict.status_code == 409


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "wrong@atlas.dev", "password": "securepass1"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@atlas.dev", "password": "incorrect1"},
    )
    assert response.status_code == 401


def test_me_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
