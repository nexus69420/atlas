"""Explainability orchestration — retrain + SHAP + persist."""

from uuid import UUID

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.storage import LocalStorage
from app.ml.explainability.shap_explainer import explain_pipeline
from app.ml.training.fit import fit_model_pipeline
from app.models.explanation import Explanation
from app.models.user import User
from app.repositories.explanation_repository import ExplanationRepository
from app.schemas.explainability import ExplainRequest
from app.services.dataset_service import DatasetService
from app.services.experiment_service import ExperimentService


class ExplainabilityService:
    def __init__(self, db: Session, storage: LocalStorage | None = None) -> None:
        self._experiments = ExperimentService(db, storage=storage)
        self._datasets = DatasetService(db, storage=storage)
        self._explanations = ExplanationRepository(db)
        self._storage = storage or LocalStorage()

    def explain(
        self,
        owner: User,
        project_id: UUID,
        experiment_id: UUID,
        payload: ExplainRequest,
    ) -> Explanation:
        experiment = self._experiments.get_for_project(owner, project_id, experiment_id)
        if experiment.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Explanations require a completed experiment",
            )

        # Ensure model was part of this experiment when results exist
        if experiment.results and experiment.results.get("models"):
            keys = {m["model_key"] for m in experiment.results["models"]}
            if payload.model_key not in keys:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Model '{payload.model_key}' was not part of this experiment. "
                        f"Available: {sorted(keys)}"
                    ),
                )

        dataset = self._datasets.get_for_project(
            owner, project_id, experiment.dataset_id
        )
        frame = pd.read_csv(self._storage.absolute_path(dataset.storage_key))

        config = experiment.config or {}
        try:
            fitted = fit_model_pipeline(
                frame,
                target_column=experiment.target_column,
                model_key=payload.model_key,
                task_type=experiment.task_type,  # type: ignore[arg-type]
                test_size=float(config.get("test_size", 0.2)),
                random_state=int(config.get("random_state", 42)),
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        x_train: pd.DataFrame = fitted["x_train"]
        x_test: pd.DataFrame = fitted["x_test"]
        n = min(payload.max_samples, len(x_train), len(x_test))
        if n < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough rows to compute SHAP explanations",
            )

        background = x_train.sample(n=n, random_state=42)
        explain_x = x_test.head(n)

        try:
            report = explain_pipeline(
                fitted["pipeline"],
                background,
                explain_x,
                instance_index=payload.instance_index,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"SHAP explanation failed: {exc}",
            ) from exc

        report["model_key"] = fitted["model_key"]
        report["model_name"] = fitted["model_name"]
        report["feature_columns_raw"] = fitted["feature_columns"]
        report["dropped_columns"] = fitted["dropped_columns"]

        return self._explanations.upsert(
            experiment_id=experiment.id,
            model_key=payload.model_key,
            report=report,
        )

    def get(
        self,
        owner: User,
        project_id: UUID,
        experiment_id: UUID,
        model_key: str,
    ) -> Explanation:
        self._experiments.get_for_project(owner, project_id, experiment_id)
        row = self._explanations.get(experiment_id, model_key)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=("Explanation not found. " "Generate one with POST .../explain"),
            )
        return row
