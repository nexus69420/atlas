"""Deployment business logic — fit, serialize, serve, export Docker bundle."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any
from uuid import UUID

import joblib
import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.storage import LocalStorage
from app.ml.deployment.bundle import write_deployment_bundle
from app.ml.training.deploy_fit import fit_production_pipeline
from app.models.deployment import Deployment
from app.models.user import User
from app.repositories.deployment_repository import DeploymentRepository
from app.schemas.deployment import (
    DeploymentCreateRequest,
    DeploymentResponse,
    PredictRequest,
    PredictResponse,
)
from app.services.dataset_service import DatasetService
from app.services.experiment_service import ExperimentService
from app.services.project_service import ProjectService


class DeploymentService:
    def __init__(self, db: Session, storage: LocalStorage | None = None) -> None:
        self._db = db
        self._deployments = DeploymentRepository(db)
        self._projects = ProjectService(db)
        self._experiments = ExperimentService(db, storage=storage)
        self._datasets = DatasetService(db, storage=storage)
        self._dataset_storage = storage or LocalStorage()
        settings = get_settings()
        self._artifact_storage = LocalStorage(root=Path(settings.artifact_storage_path))

    def _enrich(self, deployment: Deployment) -> DeploymentResponse:
        response = DeploymentResponse.model_validate(deployment)
        response.predict_path = (
            f"/api/v1/projects/{deployment.project_id}/deployments/"
            f"{deployment.id}/predict"
        )
        response.bundle_hint = (
            f"Build the exported bundle at artifact storage key "
            f"'{deployment.bundle_key}' with: docker build -t atlas-model ."
        )
        return response

    def _resolve_model_key(self, experiment: Any, requested: str | None) -> str:
        if requested:
            if experiment.results and experiment.results.get("models"):
                keys = {m["model_key"] for m in experiment.results["models"]}
                if requested not in keys:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Model '{requested}' was not part of this experiment. "
                            f"Available: {sorted(keys)}"
                        ),
                    )
            return requested

        winner = None
        if experiment.results:
            comparison = experiment.results.get("comparison") or {}
            winner_block = comparison.get("winner") or {}
            winner = winner_block.get("model_key")
        if not winner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No model_key provided and experiment has no comparison winner. "
                    "Pass model_key explicitly."
                ),
            )
        return winner

    def create(
        self,
        owner: User,
        project_id: UUID,
        payload: DeploymentCreateRequest,
    ) -> DeploymentResponse:
        project = self._projects.get_for_user(owner, project_id)
        experiment = self._experiments.get_for_project(
            owner, project_id, payload.experiment_id
        )
        if experiment.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only completed experiments can be deployed",
            )

        model_key = self._resolve_model_key(experiment, payload.model_key)
        dataset = self._datasets.get_for_project(
            owner, project_id, experiment.dataset_id
        )
        frame = pd.read_csv(self._dataset_storage.absolute_path(dataset.storage_key))

        try:
            fitted = fit_production_pipeline(
                frame,
                target_column=experiment.target_column,
                model_key=model_key,
                task_type=experiment.task_type,  # type: ignore[arg-type]
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        deployment_id = uuid.uuid4()
        artifact_key = f"{deployment_id}/model.joblib"
        bundle_key = f"{deployment_id}/bundle"

        metadata = {
            "deployment_id": str(deployment_id),
            "experiment_id": str(experiment.id),
            "project_id": str(project.id),
            "model_key": fitted["model_key"],
            "model_name": fitted["model_name"],
            "task_type": fitted["task_type"],
            "target_column": experiment.target_column,
            "feature_columns": fitted["feature_columns"],
            "dropped_columns": fitted["dropped_columns"],
            "n_rows_trained": fitted["n_rows_trained"],
            "classes": fitted["classes"],
            "trained_on": "full_dataset",
            "note": (
                "Artifact was fit on all rows with a non-null target. "
                "Experiment metrics remain the evidence for model selection."
            ),
        }

        model_path = self._artifact_storage.absolute_path(artifact_key)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(fitted["pipeline"], model_path)

        # Also persist metadata next to the model
        meta_path = self._artifact_storage.absolute_path(
            f"{deployment_id}/metadata.json"
        )
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        bundle_dir = self._artifact_storage.absolute_path(bundle_key)
        write_deployment_bundle(
            bundle_dir,
            model_path=model_path,
            metadata=metadata,
        )

        deployment = Deployment(
            id=deployment_id,
            project_id=project.id,
            experiment_id=experiment.id,
            name=payload.name.strip(),
            model_key=model_key,
            status="active",
            artifact_key=artifact_key,
            bundle_key=bundle_key,
            metadata_json=metadata,
            prediction_count=0,
        )
        deployment = self._deployments.create(deployment)
        return self._enrich(deployment)

    def list_for_project(
        self, owner: User, project_id: UUID
    ) -> list[DeploymentResponse]:
        project = self._projects.get_for_user(owner, project_id)
        rows = self._deployments.list_by_project(project.id)
        return [self._enrich(row) for row in rows]

    def get_for_project(
        self,
        owner: User,
        project_id: UUID,
        deployment_id: UUID,
    ) -> Deployment:
        project = self._projects.get_for_user(owner, project_id)
        deployment = self._deployments.get_by_id(deployment_id)
        if deployment is None or deployment.project_id != project.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deployment not found",
            )
        return deployment

    def get_response(
        self,
        owner: User,
        project_id: UUID,
        deployment_id: UUID,
    ) -> DeploymentResponse:
        return self._enrich(self.get_for_project(owner, project_id, deployment_id))

    def deactivate(
        self,
        owner: User,
        project_id: UUID,
        deployment_id: UUID,
    ) -> DeploymentResponse:
        deployment = self.get_for_project(owner, project_id, deployment_id)
        deployment.status = "inactive"
        deployment = self._deployments.save(deployment)
        return self._enrich(deployment)

    def predict(
        self,
        owner: User,
        project_id: UUID,
        deployment_id: UUID,
        payload: PredictRequest,
    ) -> PredictResponse:
        deployment = self.get_for_project(owner, project_id, deployment_id)
        if deployment.status != "active":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Deployment is inactive",
            )

        feature_columns: list[str] = list(
            deployment.metadata_json.get("feature_columns") or []
        )
        frame = pd.DataFrame(payload.instances)
        missing = [c for c in feature_columns if c not in frame.columns]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing features: {missing}",
            )
        frame = frame[feature_columns]

        model_path = self._artifact_storage.absolute_path(deployment.artifact_key)
        if not model_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model artifact missing from storage",
            )

        pipeline = joblib.load(model_path)
        predictions = pipeline.predict(frame).tolist()
        probabilities = None
        if hasattr(pipeline, "predict_proba"):
            try:
                probabilities = pipeline.predict_proba(frame).tolist()
            except Exception:
                probabilities = None

        deployment.prediction_count += len(payload.instances)
        self._deployments.save(deployment)

        return PredictResponse(
            deployment_id=deployment.id,
            model_key=deployment.model_key,
            predictions=predictions,
            probabilities=probabilities,
            feature_columns=feature_columns,
        )
