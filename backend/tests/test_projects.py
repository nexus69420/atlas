"""Project API tests — ownership and CRUD."""

from fastapi.testclient import TestClient


def test_create_list_get_project(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    create = client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"name": "Churn Baseline", "description": "First experiment workspace"},
    )
    assert create.status_code == 201
    project = create.json()
    assert project["name"] == "Churn Baseline"
    assert project["description"] == "First experiment workspace"
    assert "id" in project
    assert "owner_id" in project

    listed = client.get("/api/v1/projects", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["id"] == project["id"]

    fetched = client.get(f"/api/v1/projects/{project['id']}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Churn Baseline"


def test_update_and_delete_project(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    created = client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={"name": "Temp", "description": None},
    ).json()

    updated = client.patch(
        f"/api/v1/projects/{created['id']}",
        headers=auth_headers,
        json={"name": "Renamed", "description": "Updated"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Renamed"
    assert updated.json()["description"] == "Updated"

    deleted = client.delete(
        f"/api/v1/projects/{created['id']}",
        headers=auth_headers,
    )
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/projects/{created['id']}", headers=auth_headers)
    assert missing.status_code == 404


def test_duplicate_project_name_returns_409(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    payload = {"name": "Same Name"}
    assert (
        client.post("/api/v1/projects", headers=auth_headers, json=payload).status_code
        == 201
    )
    conflict = client.post("/api/v1/projects", headers=auth_headers, json=payload)
    assert conflict.status_code == 409


def test_projects_require_auth(client: TestClient) -> None:
    assert client.get("/api/v1/projects").status_code == 401
    assert client.post("/api/v1/projects", json={"name": "Nope"}).status_code == 401


def test_cannot_access_another_users_project(client: TestClient) -> None:
    # Owner A creates a project
    client.post(
        "/api/v1/auth/register",
        json={"email": "a@atlas.dev", "password": "securepass1"},
    )
    token_a = client.post(
        "/api/v1/auth/login",
        json={"email": "a@atlas.dev", "password": "securepass1"},
    ).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    project_id = client.post(
        "/api/v1/projects",
        headers=headers_a,
        json={"name": "Private"},
    ).json()["id"]

    # Owner B must not see it
    client.post(
        "/api/v1/auth/register",
        json={"email": "b@atlas.dev", "password": "securepass1"},
    )
    token_b = client.post(
        "/api/v1/auth/login",
        json={"email": "b@atlas.dev", "password": "securepass1"},
    ).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    assert (
        client.get(f"/api/v1/projects/{project_id}", headers=headers_b).status_code
        == 404
    )
    assert client.get("/api/v1/projects", headers=headers_b).json() == []
