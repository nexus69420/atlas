"""Experiment business logic — ownership, run orchestration, persistence."""

from uuid import UUID

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.storage import LocalStorage
from app.ml.training.experiment_runner import run_experiment
from app.models.experiment import Experiment
from app.models.user import User
from app.repositories.experiment_repository import ExperimentRepository
from app.schemas.experiment import ExperimentCreateRequest
from app.services.dataset_service import DatasetService
from app.services.project_service import ProjectService


class ExperimentService:
    def __init__(self, db: Session, storage: LocalStorage | None = None) -> None:
        self._db = db
        self._experiments = ExperimentRepository(db)
        self._projects = ProjectService(db)
        self._datasets = DatasetService(db, storage=storage)
        self._storage = storage or LocalStorage()

    def create_and_run(
        self,
        owner: User,
        project_id: UUID,
        payload: ExperimentCreateRequest,
    ) -> Experiment:
        """Create an experiment row and run it synchronously (V1).

        Why sync for V1: small CSVs finish quickly; Celery/workers come when
        jobs are long enough to need a queue.
        """
        project = self._projects.get_for_user(owner, project_id)
        dataset = self._datasets.get_for_project(owner, project_id, payload.dataset_id)

        config = {
            "test_size": payload.test_size,
            "random_state": payload.random_state,
            "models": payload.models,
        }

        experiment = Experiment(
            project_id=project.id,
            dataset_id=dataset.id,
            name=payload.name.strip(),
            status="running",
            task_type=payload.task_type,
            target_column=payload.target_column,
            config=config,
            results=None,
            error_message=None,
        )
        experiment = self._experiments.create(experiment)

        try:
            frame = pd.read_csv(self._storage.absolute_path(dataset.storage_key))
            if payload.target_column not in frame.columns:
                raise ValueError(
                    f"Target column '{payload.target_column}' not found in dataset"
                )

            results = run_experiment(
                frame,
                target_column=payload.target_column,
                task_type=payload.task_type,
                test_size=payload.test_size,
                random_state=payload.random_state,
                model_keys=payload.models,
            )
            experiment.status = "completed"
            experiment.results = results
            experiment.error_message = None
        except ValueError as exc:
            experiment.status = "failed"
            experiment.error_message = str(exc)
        except Exception as exc:  # noqa: BLE001 — persist failure, don't crash API
            experiment.status = "failed"
            experiment.error_message = f"Experiment failed: {exc}"

        return self._experiments.save(experiment)

    def list_for_project(self, owner: User, project_id: UUID) -> list[Experiment]:
        project = self._projects.get_for_user(owner, project_id)
        return self._experiments.list_by_project(project.id)

    def get_for_project(
        self,
        owner: User,
        project_id: UUID,
        experiment_id: UUID,
    ) -> Experiment:
        project = self._projects.get_for_user(owner, project_id)
        experiment = self._experiments.get_by_id(experiment_id)
        if experiment is None or experiment.project_id != project.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found",
            )
        return experiment
