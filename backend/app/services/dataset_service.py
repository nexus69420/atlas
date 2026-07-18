"""Dataset business logic — upload, metadata, preview, ownership."""

import io
import uuid
from pathlib import Path
from uuid import UUID

import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.storage import LocalStorage
from app.models.dataset import Dataset
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.dataset import DatasetPreviewResponse
from app.services.project_service import ProjectService


class DatasetService:
    def __init__(self, db: Session, storage: LocalStorage | None = None) -> None:
        self._db = db
        self._datasets = DatasetRepository(db)
        self._projects = ProjectService(db)
        self._storage = storage or LocalStorage()
        self._settings = get_settings()

    async def upload(
        self,
        owner: User,
        project_id: UUID,
        file: UploadFile,
        name: str | None = None,
    ) -> Dataset:
        project = self._projects.get_for_user(owner, project_id)

        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required",
            )

        original_filename = Path(file.filename).name
        if not original_filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV uploads are supported in V1",
            )

        data = await file.read()
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )
        if len(data) > self._settings.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    f"File exceeds max upload size "
                    f"({self._settings.max_upload_bytes} bytes)"
                ),
            )

        try:
            frame = pd.read_csv(io.BytesIO(data))
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not parse CSV file",
            ) from exc

        if frame.empty and len(frame.columns) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV has no columns",
            )

        dataset_name = (name or Path(original_filename).stem).strip()
        if not dataset_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset name is required",
            )
        if self._datasets.get_by_project_and_name(project.id, dataset_name) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A dataset with this name already exists in the project",
            )

        dataset_id = uuid.uuid4()
        storage_key = self._storage.build_key(project.id, dataset_id, ".csv")
        self._storage.save(storage_key, data)

        column_schema = [
            {"name": str(col), "dtype": str(dtype)}
            for col, dtype in frame.dtypes.items()
        ]

        dataset = Dataset(
            id=dataset_id,
            project_id=project.id,
            name=dataset_name,
            original_filename=original_filename,
            storage_key=storage_key,
            content_type=file.content_type or "text/csv",
            file_size_bytes=len(data),
            row_count=int(len(frame)),
            column_count=int(len(frame.columns)),
            column_schema=column_schema,
        )
        return self._datasets.create(dataset)

    def list_for_project(self, owner: User, project_id: UUID) -> list[Dataset]:
        project = self._projects.get_for_user(owner, project_id)
        return self._datasets.list_by_project(project.id)

    def get_for_project(
        self,
        owner: User,
        project_id: UUID,
        dataset_id: UUID,
    ) -> Dataset:
        project = self._projects.get_for_user(owner, project_id)
        dataset = self._datasets.get_by_id(dataset_id)
        if dataset is None or dataset.project_id != project.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found",
            )
        return dataset

    def preview(
        self,
        owner: User,
        project_id: UUID,
        dataset_id: UUID,
        limit: int | None = None,
    ) -> DatasetPreviewResponse:
        dataset = self.get_for_project(owner, project_id, dataset_id)
        settings = self._settings
        row_limit = (
            limit if limit is not None else settings.dataset_preview_default_rows
        )
        row_limit = max(1, min(row_limit, settings.dataset_preview_max_rows))

        try:
            frame = pd.read_csv(
                self._storage.absolute_path(dataset.storage_key),
                nrows=row_limit,
            )
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset file missing from storage",
            ) from exc

        # NaN is not valid JSON — convert to None
        records = frame.where(pd.notna(frame), None).to_dict(orient="records")
        columns = [str(c) for c in frame.columns.tolist()]

        return DatasetPreviewResponse(
            dataset_id=dataset.id,
            columns=columns,
            rows=records,
            preview_row_count=len(records),
            total_row_count=dataset.row_count,
            limit=row_limit,
        )

    def delete(self, owner: User, project_id: UUID, dataset_id: UUID) -> None:
        dataset = self.get_for_project(owner, project_id, dataset_id)
        self._storage.delete(dataset.storage_key)
        self._datasets.delete(dataset)
