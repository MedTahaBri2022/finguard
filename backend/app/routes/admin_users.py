from pydantic import BaseModel, EmailStr
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.dependencies.auth import (
    require_platform_admin,
)

from app.models.client_profile import (
    ClientProfile,
)

from app.models.user import User

from app.services.auth_service import (
    create_user,
)


router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin Users"],
)


# ============================================================
# SCHEMAS
# ============================================================


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str

    role: str = "client_member"

    is_active: bool = True


class AdminUserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None


# ============================================================
# HELPERS
# ============================================================


def serialize_user(
    user: User,
):
    return {
        "id": user.id,

        "email": user.email,

        "role": user.role,

        "client_profile_id": (
            user.client_profile_id
        ),

        "is_active": (
            user.is_active
        ),

        "created_at": (
            user.created_at
        ),

        "updated_at": (
            user.updated_at
        ),
    }


def get_client_or_404(
    db: Session,
    client_id: int,
) -> ClientProfile:
    client = (
        db.query(ClientProfile)
        .filter(
            ClientProfile.id
            == client_id
        )
        .first()
    )

    if client is None:
        raise HTTPException(
            status_code=404,
            detail="Client profile not found.",
        )

    return client


# ============================================================
# LIST CLIENT USERS
# ============================================================


@router.get(
    "/clients/{client_id}/users"
)
def list_client_users(
    client_id: int,

    db: Session = Depends(
        get_db
    ),

    current_admin: User = Depends(
        require_platform_admin
    ),
):
    client = get_client_or_404(
        db,
        client_id,
    )

    users = (
        db.query(User)
        .filter(
            User.client_profile_id
            == client.id
        )
        .order_by(
            User.id.asc()
        )
        .all()
    )

    return {
        "client": {
            "id": client.id,
            "name": client.name,
        },

        "total": len(users),

        "users": [
            serialize_user(user)
            for user in users
        ],
    }


# ============================================================
# CREATE CLIENT USER
# ============================================================


@router.post(
    "/clients/{client_id}/users",
    status_code=status.HTTP_201_CREATED,
)
def create_client_user(
    client_id: int,

    payload: AdminUserCreate,

    db: Session = Depends(
        get_db
    ),

    current_admin: User = Depends(
        require_platform_admin
    ),
):
    client = get_client_or_404(
        db,
        client_id,
    )

    allowed_roles = {
        "client_admin",
        "client_member",
    }

    role = (
        payload.role
        .strip()
        .lower()
    )

    if role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail=(
                "Client users must have "
                "role client_admin or "
                "client_member."
            ),
        )

    try:
        user = create_user(
            db,
            email=str(
                payload.email
            ),
            password=payload.password,
            role=role,
            client_profile_id=client.id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


    if (
        user.is_active
        != payload.is_active
    ):
        user.is_active = (
            payload.is_active
        )

        db.commit()
        db.refresh(user)


    return {
        "message": (
            "Client user created."
        ),

        "user": (
            serialize_user(user)
        ),
    }


# ============================================================
# UPDATE CLIENT USER
# ============================================================


@router.patch(
    "/clients/{client_id}/users/{user_id}"
)
def update_client_user(
    client_id: int,

    user_id: int,

    payload: AdminUserUpdate,

    db: Session = Depends(
        get_db
    ),

    current_admin: User = Depends(
        require_platform_admin
    ),
):
    client = get_client_or_404(
        db,
        client_id,
    )


    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.client_profile_id
            == client.id,
        )
        .first()
    )


    if user is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "User not found for "
                "this client."
            ),
        )


    if payload.role is not None:
        role = (
            payload.role
            .strip()
            .lower()
        )

        allowed_roles = {
            "client_admin",
            "client_member",
        }

        if role not in allowed_roles:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Client users must have "
                    "role client_admin or "
                    "client_member."
                ),
            )

        user.role = role


    if (
        payload.is_active
        is not None
    ):
        user.is_active = (
            payload.is_active
        )


    db.commit()
    db.refresh(user)


    return {
        "message": (
            "Client user updated."
        ),

        "user": (
            serialize_user(user)
        ),
    }