"""Schemas for the Atlas Dataset Report (profiling)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProfileGenerateRequest(BaseModel):
    """Optional target column enables class-imbalance analysis."""

    target_column: str | None = Field(default=None, max_length=200)


class DatasetProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    target_column: str | None
    report: dict[str, Any]
    created_at: datetime
    updated_at: datetime
