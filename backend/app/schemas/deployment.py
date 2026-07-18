"""Deployment API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeploymentCreateRequest(BaseModel):
    experiment_id: UUID
    name: str = Field(min_length=1, max_length=200)
    model_key: str | None = Field(
        default=None,
        description="Defaults to the experiment comparison winner when omitted",
    )


class DeploymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    experiment_id: UUID
    name: str
    model_key: str
    status: str
    artifact_key: str
    bundle_key: str
    metadata_json: dict[str, Any]
    prediction_count: int
    created_at: datetime
    updated_at: datetime
    predict_path: str | None = None
    bundle_hint: str | None = None


class PredictRequest(BaseModel):
    instances: list[dict[str, Any]] = Field(min_length=1)


class PredictResponse(BaseModel):
    deployment_id: UUID
    model_key: str
    predictions: list[Any]
    probabilities: list[list[float]] | None = None
    feature_columns: list[str]
