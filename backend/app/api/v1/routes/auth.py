"""Authentication routes — thin HTTP adapters over AuthService."""

from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep, CurrentUser
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserRegisterRequest,
    auth_service: AuthServiceDep,
) -> UserResponse:
    """Create a new user account."""
    user = auth_service.register(payload)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: UserLoginRequest,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    """Exchange email/password for a JWT access token."""
    tokens = auth_service.login(payload)
    return TokenResponse(access_token=tokens.access_token)


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser) -> UserResponse:
    """Return the currently authenticated user."""
    return UserResponse.model_validate(current_user)
