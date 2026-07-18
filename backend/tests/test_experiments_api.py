"""Experiment API tests."""

import io

from fastapi.testclient import TestClient

# Enough rows for stratified split + 3 models
_CSV_LINES = ["age,income,churn"]
for i in range(30):
    _CSV_LINES.append(f"{20 + i % 8},{25000 + i * 800},0")
for i in range(30):
    _CSV_LINES.append(f"{45 + i % 8},{70000 + i * 600},1")
CSV_BYTES = ("\n".join(_CSV_LINES) + "\n").encode()


def _upload(client: TestClient, auth_headers: dict[str, str], project_id: str) -> str:
    response = client.post(
        f"/api/v1/projects/{project_id}/datasets",
        headers=auth_headers,
        files={"file": ("train.csv", io.BytesIO(CSV_BYTES), "text/csv")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_list_get_experiment(
    client: TestClient,
    auth_headers: dict[str, str],
    project_id: str,
) -> None:
    dataset_id = _upload(client, auth_headers, project_id)

    created = client.post(
        f"/api/v1/projects/{project_id}/experiments",
        headers=auth_headers,
        json={
            "dataset_id": dataset_id,
            "name": "Baseline churn",
            "target_column": "churn",
            "task_type": "classification",
            "models": ["logistic_regression", "random_forest"],
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "completed"
    assert body["results"] is not None
    assert len(body["results"]["models"]) == 2
    assert body["results"]["comparison"]["winner"] is not None

    listed = client.get(
        f"/api/v1/projects/{project_id}/experiments",
        headers=auth_headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    fetched = client.get(
        f"/api/v1/projects/{project_id}/experiments/{body['id']}",
        headers=auth_headers,
    )
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Baseline churn"


def test_experiment_missing_target_fails_gracefully(
    client: TestClient,
    auth_headers: dict[str, str],
    project_id: str,
) -> None:
    dataset_id = _upload(client, auth_headers, project_id)
    response = client.post(
        f"/api/v1/projects/{project_id}/experiments",
        headers=auth_headers,
        json={
            "dataset_id": dataset_id,
            "name": "Bad target",
            "target_column": "nope",
            "task_type": "classification",
            "models": ["logistic_regression"],
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "failed"
    assert response.json()["error_message"]
