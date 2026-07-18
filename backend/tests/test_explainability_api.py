"""SHAP explainability API tests."""

import io

from fastapi.testclient import TestClient

_CSV_LINES = ["age,income,churn"]
for i in range(40):
    _CSV_LINES.append(f"{20 + i % 8},{25000 + i * 800},0")
for i in range(40):
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
            "name": "Explain me",
            "target_column": "churn",
            "task_type": "classification",
            "models": ["logistic_regression", "random_forest"],
        },
    )
    assert experiment.json()["status"] == "completed"
    return experiment.json()["id"]


def test_explain_and_fetch_shap(
    client: TestClient,
    auth_headers: dict[str, str],
    project_id: str,
) -> None:
    experiment_id = _setup_experiment(client, auth_headers, project_id)

    missing = client.get(
        f"/api/v1/projects/{project_id}/experiments/{experiment_id}/explanations/random_forest",
        headers=auth_headers,
    )
    assert missing.status_code == 404

    explained = client.post(
        f"/api/v1/projects/{project_id}/experiments/{experiment_id}/explain",
        headers=auth_headers,
        json={
            "model_key": "random_forest",
            "max_samples": 32,
            "instance_index": 0,
        },
    )
    assert explained.status_code == 201
    report = explained.json()["report"]
    assert report["method"] == "shap"
    assert report["feature_importances"]
    assert report["summary"]
    assert report["instance"] is not None
    assert report["instance"]["top_contributions"]

    fetched = client.get(
        f"/api/v1/projects/{project_id}/experiments/{experiment_id}/explanations/random_forest",
        headers=auth_headers,
    )
    assert fetched.status_code == 200
    assert fetched.json()["model_key"] == "random_forest"


def test_explain_rejects_unknown_model(
    client: TestClient,
    auth_headers: dict[str, str],
    project_id: str,
) -> None:
    experiment_id = _setup_experiment(client, auth_headers, project_id)
    response = client.post(
        f"/api/v1/projects/{project_id}/experiments/{experiment_id}/explain",
        headers=auth_headers,
        json={"model_key": "gradient_boosting"},
    )
    assert response.status_code == 400
