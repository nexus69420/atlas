"""Dataset upload / preview API tests."""

import io

from fastapi.testclient import TestClient

CSV_BYTES = b"age,churn\n22,0\n45,1\n31,0\n"


def test_upload_list_preview_delete(
    client: TestClient,
    auth_headers: dict[str, str],
    project_id: str,
) -> None:
    upload = client.post(
        f"/api/v1/projects/{project_id}/datasets",
        headers=auth_headers,
        files={"file": ("customer_churn.csv", io.BytesIO(CSV_BYTES), "text/csv")},
    )
    assert upload.status_code == 201
    dataset = upload.json()
    assert dataset["name"] == "customer_churn"
    assert dataset["original_filename"] == "customer_churn.csv"
    assert dataset["row_count"] == 3
    assert dataset["column_count"] == 2
    assert [c["name"] for c in dataset["column_schema"]] == ["age", "churn"]

    listed = client.get(
        f"/api/v1/projects/{project_id}/datasets",
        headers=auth_headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    preview = client.get(
        f"/api/v1/projects/{project_id}/datasets/{dataset['id']}/preview",
        headers=auth_headers,
    )
    assert preview.status_code == 200
    body = preview.json()
    assert body["columns"] == ["age", "churn"]
    assert body["preview_row_count"] == 3
    assert body["total_row_count"] == 3
    assert body["rows"][0]["age"] == 22

    deleted = client.delete(
        f"/api/v1/projects/{project_id}/datasets/{dataset['id']}",
        headers=auth_headers,
    )
    assert deleted.status_code == 204

    missing = client.get(
        f"/api/v1/projects/{project_id}/datasets/{dataset['id']}",
        headers=auth_headers,
    )
    assert missing.status_code == 404


def test_upload_rejects_non_csv(
    client: TestClient,
    auth_headers: dict[str, str],
    project_id: str,
) -> None:
    response = client.post(
        f"/api/v1/projects/{project_id}/datasets",
        headers=auth_headers,
        files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert response.status_code == 400


def test_upload_custom_name_and_duplicate(
    client: TestClient,
    auth_headers: dict[str, str],
    project_id: str,
) -> None:
    first = client.post(
        f"/api/v1/projects/{project_id}/datasets",
        headers=auth_headers,
        data={"name": "churn_v1"},
        files={"file": ("a.csv", io.BytesIO(CSV_BYTES), "text/csv")},
    )
    assert first.status_code == 201
    assert first.json()["name"] == "churn_v1"

    dup = client.post(
        f"/api/v1/projects/{project_id}/datasets",
        headers=auth_headers,
        data={"name": "churn_v1"},
        files={"file": ("b.csv", io.BytesIO(CSV_BYTES), "text/csv")},
    )
    assert dup.status_code == 409


def test_dataset_requires_auth(client: TestClient) -> None:
    response = client.get(
        "/api/v1/projects/00000000-0000-0000-0000-000000000001/datasets"
    )
    assert response.status_code == 401
