"""Health check endpoint.

Kept intentionally simple for Sprint 1.
Later we can split:
- GET /health          → liveness (process is up)
- GET /health/ready    → readiness (DB, Redis, etc. reachable)
"""

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return service liveness status."""
    return HealthResponse(status="healthy")
