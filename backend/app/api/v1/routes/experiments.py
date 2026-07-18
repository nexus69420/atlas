"""Experiment routes — create/run, list, get, compare, explain."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, ExperimentServiceDep, ExplainabilityServiceDep
from app.schemas.comparison import ExperimentComparisonResponse
from app.schemas.experiment import (
    ExperimentCreateRequest,
    ExperimentResponse,
    ExperimentSummaryResponse,
)
from app.schemas.explainability import ExplainRequest, ExplanationResponse
from app.services.comparison_service import build_comparison_response

router = APIRouter(prefix="/projects/{project_id}/experiments", tags=["experiments"])


@router.post(
    "",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_experiment(
    project_id: UUID,
    payload: ExperimentCreateRequest,
    current_user: CurrentUser,
    experiment_service: ExperimentServiceDep,
) -> ExperimentResponse:
    """Run a multi-model experiment synchronously and return stored results."""
    experiment = experiment_service.create_and_run(current_user, project_id, payload)
    return ExperimentResponse.model_validate(experiment)


@router.get("", response_model=list[ExperimentSummaryResponse])
def list_experiments(
    project_id: UUID,
    current_user: CurrentUser,
    experiment_service: ExperimentServiceDep,
) -> list[ExperimentSummaryResponse]:
    experiments = experiment_service.list_for_project(current_user, project_id)
    return [ExperimentSummaryResponse.model_validate(e) for e in experiments]


@router.get("/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(
    project_id: UUID,
    experiment_id: UUID,
    current_user: CurrentUser,
    experiment_service: ExperimentServiceDep,
) -> ExperimentResponse:
    experiment = experiment_service.get_for_project(
        current_user, project_id, experiment_id
    )
    return ExperimentResponse.model_validate(experiment)


@router.get(
    "/{experiment_id}/comparison",
    response_model=ExperimentComparisonResponse,
)
def get_experiment_comparison(
    project_id: UUID,
    experiment_id: UUID,
    current_user: CurrentUser,
    experiment_service: ExperimentServiceDep,
) -> ExperimentComparisonResponse:
    """Polished model comparison view for UI / decision-making."""
    experiment = experiment_service.get_for_project(
        current_user, project_id, experiment_id
    )
    return build_comparison_response(experiment)


@router.post(
    "/{experiment_id}/explain",
    response_model=ExplanationResponse,
    status_code=status.HTTP_201_CREATED,
)
def explain_experiment_model(
    project_id: UUID,
    experiment_id: UUID,
    payload: ExplainRequest,
    current_user: CurrentUser,
    explainability_service: ExplainabilityServiceDep,
) -> ExplanationResponse:
    """Generate (or regenerate) a SHAP explanation for one model in the experiment."""
    explanation = explainability_service.explain(
        current_user, project_id, experiment_id, payload
    )
    return ExplanationResponse.model_validate(explanation)


@router.get(
    "/{experiment_id}/explanations/{model_key}",
    response_model=ExplanationResponse,
)
def get_explanation(
    project_id: UUID,
    experiment_id: UUID,
    model_key: str,
    current_user: CurrentUser,
    explainability_service: ExplainabilityServiceDep,
) -> ExplanationResponse:
    explanation = explainability_service.get(
        current_user, project_id, experiment_id, model_key
    )
    return ExplanationResponse.model_validate(explanation)
