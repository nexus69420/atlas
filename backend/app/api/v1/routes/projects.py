"""Project routes — authenticated CRUD for ML workspaces."""

from uuid import UUID

from fastapi import APIRouter, Response, status

from app.api.deps import CurrentUser, ProjectServiceDep
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    payload: ProjectCreateRequest,
    current_user: CurrentUser,
    project_service: ProjectServiceDep,
) -> ProjectResponse:
    project = project_service.create(current_user, payload)
    return ProjectResponse.model_validate(project)


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    current_user: CurrentUser,
    project_service: ProjectServiceDep,
) -> list[ProjectResponse]:
    projects = project_service.list_for_user(current_user)
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    current_user: CurrentUser,
    project_service: ProjectServiceDep,
) -> ProjectResponse:
    project = project_service.get_for_user(current_user, project_id)
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    payload: ProjectUpdateRequest,
    current_user: CurrentUser,
    project_service: ProjectServiceDep,
) -> ProjectResponse:
    project = project_service.update(current_user, project_id, payload)
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    current_user: CurrentUser,
    project_service: ProjectServiceDep,
) -> Response:
    project_service.delete(current_user, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
