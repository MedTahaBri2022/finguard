import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from dotenv import load_dotenv
from jwt import InvalidTokenError
from pwdlib import PasswordHash


load_dotenv()


JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

password_hasher = PasswordHash.recommended()


# ============================================================
# JWT CONFIGURATION
# ============================================================

def get_jwt_secret_key() -> str:
    secret_key = os.getenv("JWT_SECRET_KEY")

    if not secret_key:
        raise RuntimeError(
            "JWT_SECRET_KEY is not configured."
        )

    # HS256 should use a sufficiently strong secret.
    if len(secret_key) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must contain at least 32 characters."
        )

    return secret_key


# ============================================================
# PASSWORD SECURITY
# ============================================================

def validate_password_strength(password: str) -> None:
    """
    Basic password policy for newly created/changed passwords.

    Existing password hashes remain compatible.
    """

    if len(password) < 10:
        raise ValueError(
            "Password must contain at least 10 characters."
        )

    if not any(char.isupper() for char in password):
        raise ValueError(
            "Password must contain at least one uppercase letter."
        )

    if not any(char.islower() for char in password):
        raise ValueError(
            "Password must contain at least one lowercase letter."
        )

    if not any(char.isdigit() for char in password):
        raise ValueError(
            "Password must contain at least one number."
        )

    if not any(not char.isalnum() for char in password):
        raise ValueError(
            "Password must contain at least one special character."
        )


def hash_password(password: str) -> str:
    validate_password_strength(password)

    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    try:
        return password_hasher.verify(
            plain_password,
            hashed_password,
        )
    except Exception:
        # Never expose password/hash implementation errors.
        return False


# ============================================================
# ACCESS TOKENS
# ============================================================

def create_access_token(
    *,
    subject: str,
    extra_claims: dict[str, Any] | None = None,
    expires_minutes: int | None = None,
) -> str:

    if not subject:
        raise ValueError(
            "Token subject cannot be empty."
        )

    now = datetime.now(timezone.utc)

    lifetime = (
        expires_minutes
        if expires_minutes is not None
        else ACCESS_TOKEN_EXPIRE_MINUTES
    )

    if lifetime <= 0:
        raise ValueError(
            "Token expiration must be greater than zero."
        )

    expire = now + timedelta(minutes=lifetime)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "access",
    }

    if extra_claims:
        # Prevent callers from replacing security-critical claims.
        protected_claims = {
            "sub",
            "iat",
            "exp",
            "type",
        }

        safe_claims = {
            key: value
            for key, value in extra_claims.items()
            if key not in protected_claims
        }

        payload.update(safe_claims)

    return jwt.encode(
        payload,
        get_jwt_secret_key(),
        algorithm=JWT_ALGORITHM,
    )


# ============================================================
# TOKEN VALIDATION
# ============================================================

def decode_access_token(
    token: str,
) -> dict[str, Any]:

    if not token:
        raise ValueError(
            "Access token is missing."
        )

    try:
        payload = jwt.decode(
            token,
            get_jwt_secret_key(),
            algorithms=[JWT_ALGORITHM],
            options={
                "require": [
                    "sub",
                    "iat",
                    "exp",
                    "type",
                ]
            },
        )

    except InvalidTokenError as exc:
        raise ValueError(
            "Invalid or expired access token."
        ) from exc

    if payload.get("type") != "access":
        raise ValueError(
            "Invalid token type."
        )

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject.strip():
        raise ValueError(
            "Invalid token subject."
        )

    return payload