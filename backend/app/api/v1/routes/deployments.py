"""Deployment routes — create, list, get, predict, deactivate."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DeploymentServiceDep
from app.schemas.deployment import (
    DeploymentCreateRequest,
    DeploymentResponse,
    PredictRequest,
    PredictResponse,
)

router = APIRouter(prefix="/projects/{project_id}/deployments", tags=["deployments"])


@router.post(
    "",
    response_model=DeploymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deployment(
    project_id: UUID,
    payload: DeploymentCreateRequest,
    current_user: CurrentUser,
    deployment_service: DeploymentServiceDep,
) -> DeploymentResponse:
    """Fit the selected/winning model on full data, persist artifact + Docker bundle."""
    return deployment_service.create(current_user, project_id, payload)


@router.get("", response_model=list[DeploymentResponse])
def list_deployments(
    project_id: UUID,
    current_user: CurrentUser,
    deployment_service: DeploymentServiceDep,
) -> list[DeploymentResponse]:
    return deployment_service.list_for_project(current_user, project_id)


@router.get("/{deployment_id}", response_model=DeploymentResponse)
def get_deployment(
    project_id: UUID,
    deployment_id: UUID,
    current_user: CurrentUser,
    deployment_service: DeploymentServiceDep,
) -> DeploymentResponse:
    return deployment_service.get_response(current_user, project_id, deployment_id)


@router.post("/{deployment_id}/predict", response_model=PredictResponse)
def predict(
    project_id: UUID,
    deployment_id: UUID,
    payload: PredictRequest,
    current_user: CurrentUser,
    deployment_service: DeploymentServiceDep,
) -> PredictResponse:
    return deployment_service.predict(current_user, project_id, deployment_id, payload)


@router.post(
    "/{deployment_id}/deactivate",
    response_model=DeploymentResponse,
)
def deactivate_deployment(
    project_id: UUID,
    deployment_id: UUID,
    current_user: CurrentUser,
    deployment_service: DeploymentServiceDep,
) -> DeploymentResponse:
    return deployment_service.deactivate(current_user, project_id, deployment_id)
