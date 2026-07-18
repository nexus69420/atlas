"""Dataset routes — upload CSV, list, preview, delete within a project."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, Query, Response, UploadFile, status

from app.api.deps import CurrentUser, DatasetServiceDep, ProfilingServiceDep
from app.schemas.dataset import DatasetPreviewResponse, DatasetResponse
from app.schemas.profiling import DatasetProfileResponse, ProfileGenerateRequest

router = APIRouter(prefix="/projects/{project_id}/datasets", tags=["datasets"])


@router.post(
    "",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    project_id: UUID,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
    file: Annotated[UploadFile, File()],
    name: Annotated[str | None, Form()] = None,
) -> DatasetResponse:
    """Upload a CSV into a project. Optional `name` overrides the filename stem."""
    dataset = await dataset_service.upload(current_user, project_id, file, name=name)
    return DatasetResponse.model_validate(dataset)


@router.get("", response_model=list[DatasetResponse])
def list_datasets(
    project_id: UUID,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
) -> list[DatasetResponse]:
    datasets = dataset_service.list_for_project(current_user, project_id)
    return [DatasetResponse.model_validate(d) for d in datasets]


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    project_id: UUID,
    dataset_id: UUID,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
) -> DatasetResponse:
    dataset = dataset_service.get_for_project(current_user, project_id, dataset_id)
    return DatasetResponse.model_validate(dataset)


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def preview_dataset(
    project_id: UUID,
    dataset_id: UUID,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
    limit: int | None = Query(default=None, ge=1, le=100),
) -> DatasetPreviewResponse:
    return dataset_service.preview(current_user, project_id, dataset_id, limit=limit)


@router.post(
    "/{dataset_id}/profile",
    response_model=DatasetProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_profile(
    project_id: UUID,
    dataset_id: UUID,
    current_user: CurrentUser,
    profiling_service: ProfilingServiceDep,
    payload: ProfileGenerateRequest | None = None,
) -> DatasetProfileResponse:
    """Generate (or regenerate) an Atlas Report for this dataset."""
    body = payload or ProfileGenerateRequest()
    profile = profiling_service.generate(
        current_user,
        project_id,
        dataset_id,
        target_column=body.target_column,
    )
    return DatasetProfileResponse.model_validate(profile)


@router.get("/{dataset_id}/profile", response_model=DatasetProfileResponse)
def get_profile(
    project_id: UUID,
    dataset_id: UUID,
    current_user: CurrentUser,
    profiling_service: ProfilingServiceDep,
) -> DatasetProfileResponse:
    profile = profiling_service.get(current_user, project_id, dataset_id)
    return DatasetProfileResponse.model_validate(profile)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    project_id: UUID,
    dataset_id: UUID,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
) -> Response:
    dataset_service.delete(current_user, project_id, dataset_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
