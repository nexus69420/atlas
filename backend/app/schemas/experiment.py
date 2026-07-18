"""Experiment API schemas."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExperimentCreateRequest(BaseModel):
    dataset_id: UUID
    name: str = Field(min_length=1, max_length=200)
    target_column: str = Field(min_length=1, max_length=200)
    task_type: Literal["classification", "regression"] = "classification"
    test_size: float = Field(default=0.2, ge=0.05, le=0.5)
    random_state: int = Field(default=42, ge=0)
    models: list[str] | None = Field(
        default=None,
        description="Optional subset of model keys; defaults to the full V1 registry",
    )


class ExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    dataset_id: UUID
    name: str
    status: str
    task_type: str
    target_column: str
    config: dict[str, Any]
    results: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ExperimentSummaryResponse(BaseModel):
    """Lighter list payload — omits full results for faster project listings."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    dataset_id: UUID
    name: str
    status: str
    task_type: str
    target_column: str
    created_at: datetime
    updated_at: datetime
