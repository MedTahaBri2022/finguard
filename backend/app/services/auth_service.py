from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.client_profile import ClientProfile
from app.models.user import User


VALID_ROLES = {
    "platform_admin",
    "client_admin",
    "client_member",
}


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    normalized_email = normalize_email(email)

    return (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )


def authenticate_user(
    db: Session,
    *,
    email: str,
    password: str,
) -> User | None:
    user = get_user_by_email(
        db,
        email,
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user


def validate_user_tenant_assignment(
    db: Session,
    *,
    role: str,
    client_profile_id: int | None,
) -> None:
    if role not in VALID_ROLES:
        raise ValueError(
            f"Invalid role: {role}"
        )

    if role == "platform_admin":
        if client_profile_id is not None:
            raise ValueError(
                "platform_admin must not have a client_profile_id."
            )

        return

    if client_profile_id is None:
        raise ValueError(
            f"{role} requires a client_profile_id."
        )

    client = (
        db.query(ClientProfile)
        .filter(
            ClientProfile.id == client_profile_id,
            ClientProfile.is_active.is_(True),
        )
        .first()
    )

    if client is None:
        raise ValueError(
            "Client profile does not exist or is inactive."
        )


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    role: str,
    client_profile_id: int | None = None,
) -> User:
    normalized_email = normalize_email(email)

    existing_user = get_user_by_email(
        db,
        normalized_email,
    )

    if existing_user is not None:
        raise ValueError(
            "A user with this email already exists."
        )

    if len(password) < 8:
        raise ValueError(
            "Password must contain at least 8 characters."
        )

    validate_user_tenant_assignment(
        db,
        role=role,
        client_profile_id=client_profile_id,
    )

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        role=role,
        client_profile_id=client_profile_id,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user