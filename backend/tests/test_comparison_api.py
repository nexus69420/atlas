"""Model comparison API polish tests."""

import io

from fastapi.testclient import TestClient

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
            "name": "Compare me",
            "target_column": "churn",
            "task_type": "classification",
            "models": ["logistic_regression", "random_forest"],
        },
    )
    assert experiment.status_code == 201
    assert experiment.json()["status"] == "completed"
    return experiment.json()["id"]


def test_comparison_endpoint_returns_cards_and_table(
    client: TestClient,
    auth_headers: dict[str, str],
    project_id: str,
) -> None:
    experiment_id = _setup_experiment(client, auth_headers, project_id)

    response = client.get(
        f"/api/v1/projects/{project_id}/experiments/{experiment_id}/comparison",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["primary_metric"] == "f1_macro"
    assert body["winner"] is not None
    assert len(body["models"]) == 2
    assert body["models"][0]["rank"] == 1
    assert "pros" in body["models"][0]
    assert "cons" in body["models"][0]
    assert len(body["metric_table"]) == 2
    assert "tradeoffs" in body
    assert body["metric_table"][0]["model_key"]


def test_list_experiments_is_summary(
    client: TestClient,
    auth_headers: dict[str, str],
    project_id: str,
) -> None:
    _setup_experiment(client, auth_headers, project_id)
    listed = client.get(
        f"/api/v1/projects/{project_id}/experiments",
        headers=auth_headers,
    )
    assert listed.status_code == 200
    assert "results" not in listed.json()[0]
    assert "name" in listed.json()[0]
