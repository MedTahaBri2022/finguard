from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
)
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ClientSummary,
    LoginRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import authenticate_user


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


def build_user_response(
    user: User,
) -> UserResponse:
    client = None

    if user.client_profile is not None:
        client = ClientSummary(
            id=user.client_profile.id,
            name=user.client_profile.name,
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        client_profile_id=user.client_profile_id,
        is_active=user.is_active,
        client=client,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = authenticate_user(
        db,
        email=str(payload.email),
        password=payload.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={
            "role": user.role,
            "client_profile_id": user.client_profile_id,
        },
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=(
            ACCESS_TOKEN_EXPIRE_MINUTES * 60
        ),
        user=build_user_response(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
) -> UserResponse:
    return build_user_response(
        current_user
    )