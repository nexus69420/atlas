#!/usr/bin/env python3
"""End-to-end churn demo against the in-process API (no server required).

Downloads a public Telco Customer Churn CSV when online; otherwise builds a
realistic synthetic fallback so CI / offline demos still pass.

Usage (from backend/ with venv active):

    python scripts/e2e_churn_flow.py
    python scripts/e2e_churn_flow.py --offline
"""

from __future__ import annotations

import argparse
import io
import sys
import tempfile
import urllib.request
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Allow `python scripts/e2e_churn_flow.py` from backend/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402, F401
    Dataset,
    DatasetProfile,
    Deployment,
    Experiment,
    Explanation,
    PredictionLog,
    Project,
    User,
)

TELCO_URL = (
    "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/"
    "master/data/Telco-Customer-Churn.csv"
)


def _synthetic_churn(n: int = 400) -> bytes:
    """Fallback dataset shaped like a simple churn problem."""
    rows = ["tenure,monthly_charges,total_charges,contract_month_to_month,churn"]
    for i in range(n // 2):
        tenure = 1 + (i % 12)
        monthly = 20 + (i % 40)
        rows.append(
            f"{tenure},{monthly},{tenure * monthly},1,{1 if tenure < 6 else 0}"
        )
    for i in range(n // 2):
        tenure = 12 + (i % 48)
        monthly = 40 + (i % 60)
        rows.append(
            f"{tenure},{monthly},{tenure * monthly},0,{1 if monthly > 90 else 0}"
        )
    return ("\n".join(rows) + "\n").encode()


def load_churn_csv(*, offline: bool) -> tuple[bytes, str, str]:
    """Return (csv_bytes, filename, target_column)."""
    if offline:
        return _synthetic_churn(), "synthetic_churn.csv", "churn"

    try:
        with urllib.request.urlopen(TELCO_URL, timeout=30) as resp:
            raw = resp.read()
        frame = pd.read_csv(io.BytesIO(raw))
        # Drop high-cardinality id; coerce TotalCharges; binary target
        if "customerID" in frame.columns:
            frame = frame.drop(columns=["customerID"])
        if "TotalCharges" in frame.columns:
            frame["TotalCharges"] = pd.to_numeric(frame["TotalCharges"], errors="coerce")
        if "Churn" in frame.columns:
            frame["Churn"] = (frame["Churn"].astype(str).str.lower() == "yes").astype(int)
            target = "Churn"
        else:
            raise ValueError("Expected Churn column")
        # Keep size reasonable for a sync demo
        if len(frame) > 1500:
            frame = frame.sample(n=1500, random_state=42)
        buf = io.BytesIO()
        frame.to_csv(buf, index=False)
        print(f"[e2e] downloaded telco churn: {len(frame)} rows, {len(frame.columns)} cols")
        return buf.getvalue(), "telco_churn.csv", target
    except Exception as exc:  # noqa: BLE001
        print(f"[e2e] download failed ({exc}); using synthetic churn")
        return _synthetic_churn(), "synthetic_churn.csv", "churn"


def main() -> int:
    parser = argparse.ArgumentParser(description="Atlas churn E2E demo")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip network; use synthetic CSV only",
    )
    args = parser.parse_args()

    csv_bytes, filename, target = load_churn_csv(offline=args.offline)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        get_settings.cache_clear()
        import os

        os.environ["STORAGE_PATH"] = str(tmp_path / "datasets")
        os.environ["ARTIFACT_STORAGE_PATH"] = str(tmp_path / "artifacts")
        get_settings.cache_clear()

        engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        session = SessionLocal()

        def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                assert client.get("/health").json()["status"] == "healthy"

                reg = client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": "e2e@atlas.dev",
                        "password": "securepass1",
                        "full_name": "E2E Runner",
                    },
                )
                assert reg.status_code in (201, 400), reg.text

                token = client.post(
                    "/api/v1/auth/login",
                    json={"email": "e2e@atlas.dev", "password": "securepass1"},
                ).json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                project = client.post(
                    "/api/v1/projects",
                    headers=headers,
                    json={
                        "name": "Churn E2E",
                        "description": "Hire-ready real-data path",
                    },
                )
                assert project.status_code == 201, project.text
                project_id = project.json()["id"]

                dataset = client.post(
                    f"/api/v1/projects/{project_id}/datasets",
                    headers=headers,
                    files={"file": (filename, io.BytesIO(csv_bytes), "text/csv")},
                )
                assert dataset.status_code == 201, dataset.text
                dataset_id = dataset.json()["id"]

                profile = client.post(
                    f"/api/v1/projects/{project_id}/datasets/{dataset_id}/profile",
                    headers=headers,
                )
                assert profile.status_code == 201, profile.text
                print(
                    f"[e2e] profile keys="
                    f"{list((profile.json().get('report') or {}).keys())[:6]}"
                )

                experiment = client.post(
                    f"/api/v1/projects/{project_id}/experiments",
                    headers=headers,
                    json={
                        "dataset_id": dataset_id,
                        "name": "Churn baseline",
                        "target_column": target,
                        "task_type": "classification",
                        "models": ["logistic_regression", "random_forest"],
                    },
                )
                assert experiment.status_code == 201, experiment.text
                exp = experiment.json()
                assert exp["status"] == "completed", exp.get("error_message")
                winner = exp["results"]["comparison"]["winner"]["model_key"]
                print(f"[e2e] experiment winner={winner}")
                assert "artifacts" in exp["results"]

                explain = client.post(
                    f"/api/v1/projects/{project_id}/experiments/{exp['id']}/explain",
                    headers=headers,
                    json={"model_key": winner},
                )
                assert explain.status_code == 201, explain.text
                print("[e2e] SHAP explanation stored")

                deployment = client.post(
                    f"/api/v1/projects/{project_id}/deployments",
                    headers=headers,
                    json={
                        "experiment_id": exp["id"],
                        "name": "Churn API",
                        "model_key": winner,
                    },
                )
                assert deployment.status_code == 201, deployment.text
                dep = deployment.json()
                features = dep["metadata_json"]["feature_columns"]

                # Build one predict instance from the CSV header row values
                frame = pd.read_csv(io.BytesIO(csv_bytes))
                sample = frame.iloc[0]
                instance = {
                    c: (None if pd.isna(sample[c]) else sample[c])
                    for c in features
                }
                # JSON-serialize numpy/pandas scalars
                for k, v in list(instance.items()):
                    if hasattr(v, "item"):
                        instance[k] = v.item()

                predicted = client.post(
                    f"/api/v1/projects/{project_id}/deployments/{dep['id']}/predict",
                    headers=headers,
                    json={"instances": [instance]},
                )
                assert predicted.status_code == 200, predicted.text
                print(f"[e2e] prediction={predicted.json()['predictions']}")

                logs = client.get(
                    f"/api/v1/projects/{project_id}/deployments/{dep['id']}/predictions",
                    headers=headers,
                )
                assert logs.status_code == 200
                assert len(logs.json()) >= 1
                print("[e2e] prediction log OK")
                print("[e2e] PASS - profile -> experiment -> SHAP -> deploy -> predict")
                return 0
        finally:
            app.dependency_overrides.clear()
            session.close()
            get_settings.cache_clear()


if __name__ == "__main__":
    raise SystemExit(main())
