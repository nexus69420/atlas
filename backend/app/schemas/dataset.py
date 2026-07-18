"""Dataset request/response schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ColumnSchemaItem(BaseModel):
    name: str
    dtype: str


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    original_filename: str
    content_type: str
    file_size_bytes: int
    row_count: int
    column_count: int
    column_schema: list[ColumnSchemaItem]
    created_at: datetime
    updated_at: datetime


class DatasetPreviewResponse(BaseModel):
    dataset_id: UUID
    columns: list[str]
    rows: list[dict[str, Any]]
    preview_row_count: int
    total_row_count: int
    limit: int = Field(description="Requested max preview rows")
