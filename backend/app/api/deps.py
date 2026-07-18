"""Shared FastAPI dependencies (auth context, DB session)."""

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.dataset_service import DatasetService
from app.services.deployment_service import DeploymentService
from app.services.experiment_service import ExperimentService
from app.services.explainability_service import ExplainabilityService
from app.services.profiling_service import ProfilingService
from app.services.project_service import ProjectService

# auto_error=False so missing credentials become our own 401 shape
bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_auth_service(db: DbSession) -> AuthService:
    return AuthService(db)


def get_project_service(db: DbSession) -> ProjectService:
    return ProjectService(db)


def get_dataset_service(db: DbSession) -> DatasetService:
    return DatasetService(db)


def get_profiling_service(db: DbSession) -> ProfilingService:
    return ProfilingService(db)


def get_experiment_service(db: DbSession) -> ExperimentService:
    return ExperimentService(db)


def get_explainability_service(db: DbSession) -> ExplainabilityService:
    return ExplainabilityService(db)


def get_deployment_service(db: DbSession) -> DeploymentService:
    return DeploymentService(db)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
DatasetServiceDep = Annotated[DatasetService, Depends(get_dataset_service)]
ProfilingServiceDep = Annotated[ProfilingService, Depends(get_profiling_service)]
ExperimentServiceDep = Annotated[ExperimentService, Depends(get_experiment_service)]
ExplainabilityServiceDep = Annotated[
    ExplainabilityService, Depends(get_explainability_service)
]
DeploymentServiceDep = Annotated[DeploymentService, Depends(get_deployment_service)]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_service: AuthServiceDep,
) -> User:
    """Resolve the authenticated user from a Bearer JWT."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")
        if subject is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = UUID(subject)
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return auth_service.get_user(user_id)


CurrentUser = Annotated[User, Depends(get_current_user)]
