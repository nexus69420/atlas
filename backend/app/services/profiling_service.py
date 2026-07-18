"""Orchestrate dataset profiling — ownership, I/O, persistence."""

from uuid import UUID

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.storage import LocalStorage
from app.ml.profiling.profiler import profile_dataframe
from app.models.dataset_profile import DatasetProfile
from app.models.user import User
from app.repositories.dataset_profile_repository import DatasetProfileRepository
from app.services.dataset_service import DatasetService


class ProfilingService:
    def __init__(self, db: Session, storage: LocalStorage | None = None) -> None:
        self._datasets = DatasetService(db, storage=storage)
        self._profiles = DatasetProfileRepository(db)
        self._storage = storage or LocalStorage()

    def generate(
        self,
        owner: User,
        project_id: UUID,
        dataset_id: UUID,
        target_column: str | None = None,
    ) -> DatasetProfile:
        dataset = self._datasets.get_for_project(owner, project_id, dataset_id)

        try:
            frame = pd.read_csv(self._storage.absolute_path(dataset.storage_key))
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset file missing from storage",
            ) from exc

        if target_column is not None and target_column not in frame.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target column '{target_column}' not found in dataset",
            )

        report = profile_dataframe(frame, target_column=target_column)
        return self._profiles.upsert(
            dataset_id=dataset.id,
            target_column=target_column,
            report=report,
        )

    def get(
        self,
        owner: User,
        project_id: UUID,
        dataset_id: UUID,
    ) -> DatasetProfile:
        # Ownership check via dataset access
        self._datasets.get_for_project(owner, project_id, dataset_id)
        profile = self._profiles.get_by_dataset_id(dataset_id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Generate one with POST .../profile",
            )
        return profile
