"""Schemas for the health endpoint."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Liveness payload returned by GET /health."""

    model_config = ConfigDict(frozen=True)

    status: Literal["healthy"]
