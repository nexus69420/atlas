"""Explainability API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExplainRequest(BaseModel):
    model_key: str = Field(min_length=1, max_length=100)
    max_samples: int = Field(
        default=64,
        ge=10,
        le=500,
        description="Rows used for SHAP background + explanation sample",
    )
    instance_index: int | None = Field(
        default=None,
        ge=0,
        description="Optional row index within the explained sample for local SHAP",
    )


class ExplanationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experiment_id: UUID
    model_key: str
    report: dict[str, Any]
    created_at: datetime
    updated_at: datetime
