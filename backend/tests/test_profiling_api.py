"""Profiling API tests — generate and fetch Atlas Reports."""

import io

from fastapi.testclient import TestClient

CSV_BYTES = (
    b"age,income,income_copy,churn\n"
    b"22,30000,30100,0\n"
    b"45,90000,89900,0\n"
    b"31,55000,55200,0\n"
    b"28,48000,47800,0\n"
    b",70000,70100,0\n"
    b"40,85000,84800,1\n"
)


def _upload_dataset(
    client: TestClient,
    auth_headers: dict[str, str],
    project_id: str,
) -> str:
    upload = client.post(
        f"/api/v1/projects/{project_id}/datasets",
        headers=auth_headers,
        files={"file": ("churn.csv", io.BytesIO(CSV_BYTES), "text/csv")},
    )
    assert upload.status_code == 201
    return upload.json()["id"]


def test_generate_and_get_profile(
    client: TestClient,
    auth_headers: dict[str, str],
    project_id: str,
) -> None:
    dataset_id = _upload_dataset(client, auth_headers, project_id)

    missing = client.get(
        f"/api/v1/projects/{project_id}/datasets/{dataset_id}/profile",
        headers=auth_headers,
    )
    assert missing.status_code == 404

    generated = client.post(
        f"/api/v1/projects/{project_id}/datasets/{dataset_id}/profile",
        headers=auth_headers,
        json={"target_column": "churn"},
    )
    assert generated.status_code == 201
    body = generated.json()
    assert body["dataset_id"] == dataset_id
    assert body["target_column"] == "churn"
    assert "summary" in body["report"]
    assert "warnings" in body["report"]
    assert body["report"]["target_analysis"]["column"] == "churn"

    fetched = client.get(
        f"/api/v1/projects/{project_id}/datasets/{dataset_id}/profile",
        headers=auth_headers,
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


def test_invalid_target_column_returns_400(
    client: TestClient,
    auth_headers: dict[str, str],
    project_id: str,
) -> None:
    dataset_id = _upload_dataset(client, auth_headers, project_id)
    response = client.post(
        f"/api/v1/projects/{project_id}/datasets/{dataset_id}/profile",
        headers=auth_headers,
        json={"target_column": "not_a_column"},
    )
    assert response.status_code == 400
