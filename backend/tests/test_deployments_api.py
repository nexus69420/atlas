"""Deployment API tests — create, predict, deactivate, Docker bundle files."""

import io
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import get_settings

_CSV_LINES = ["age,income,churn"]
for i in range(30):
    _CSV_LINES.append(f"{20 + i % 8},{25000 + i * 800},0")
for i in range(30):
    _CSV_LINES.append(f"{45 + i % 8},{70000 + i * 600},1")
CSV_BYTES = ("\n".join(_CSV_LINES) + "\n").encode()


def _setup_experiment(
    client: TestClient,
    auth_headers: dict[str, str],
    project_id: str,
) -> str:
    dataset_id = client.post(
        f"/api/v1/projects/{project_id}/datasets",
        headers=auth_headers,
        files={"file": ("train.csv", io.BytesIO(CSV_BYTES), "text/csv")},
    ).json()["id"]

    experiment = client.post(
        f"/api/v1/projects/{project_id}/experiments",
        headers=auth_headers,
        json={
            "dataset_id": dataset_id,
            "name": "Deployable",
            "target_column": "churn",
            "task_type": "classification",
            "models": ["logistic_regression", "random_forest"],
        },
    )
    assert experiment.json()["status"] == "completed"
    return experiment.json()["id"]


def test_deploy_predict_deactivate(
    client: TestClient,
    auth_headers: dict[str, str],
    project_id: str,
) -> None:
    experiment_id = _setup_experiment(client, auth_headers, project_id)

    created = client.post(
        f"/api/v1/projects/{project_id}/deployments",
        headers=auth_headers,
        json={
            "experiment_id": experiment_id,
            "name": "Churn API v1",
            # omit model_key → use winner
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "active"
    assert body["model_key"]
    assert body["predict_path"]
    assert body["metadata_json"]["feature_columns"] == ["age", "income"]

    # Bundle files exist on disk
    settings = get_settings()
    bundle_dir = Path(settings.artifact_storage_path) / body["bundle_key"]
    assert (bundle_dir / "Dockerfile").exists()
    assert (bundle_dir / "model.joblib").exists()
    assert (bundle_dir / "app" / "main.py").exists()

    predicted = client.post(
        f"/api/v1/projects/{project_id}/deployments/{body['id']}/predict",
        headers=auth_headers,
        json={
            "instances": [{"age": 50, "income": 75000}, {"age": 22, "income": 28000}]
        },
    )
    assert predicted.status_code == 200
    pred_body = predicted.json()
    assert len(pred_body["predictions"]) == 2
    assert pred_body["probabilities"] is not None

    fetched = client.get(
        f"/api/v1/projects/{project_id}/deployments/{body['id']}",
        headers=auth_headers,
    )
    assert fetched.json()["prediction_count"] == 2

    deactivated = client.post(
        f"/api/v1/projects/{project_id}/deployments/{body['id']}/deactivate",
        headers=auth_headers,
    )
    assert deactivated.json()["status"] == "inactive"

    blocked = client.post(
        f"/api/v1/projects/{project_id}/deployments/{body['id']}/predict",
        headers=auth_headers,
        json={"instances": [{"age": 50, "income": 75000}]},
    )
    assert blocked.status_code == 409


def test_deploy_missing_features_returns_400(
    client: TestClient,
    auth_headers: dict[str, str],
    project_id: str,
) -> None:
    experiment_id = _setup_experiment(client, auth_headers, project_id)
    deployment_id = client.post(
        f"/api/v1/projects/{project_id}/deployments",
        headers=auth_headers,
        json={
            "experiment_id": experiment_id,
            "name": "Strict",
            "model_key": "logistic_regression",
        },
    ).json()["id"]

    response = client.post(
        f"/api/v1/projects/{project_id}/deployments/{deployment_id}/predict",
        headers=auth_headers,
        json={"instances": [{"age": 40}]},
    )
    assert response.status_code == 400
