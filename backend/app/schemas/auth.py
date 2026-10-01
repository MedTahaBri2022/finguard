from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


UserRole = Literal[
    "platform_admin",
    "client_admin",
    "client_member",
]


class LoginRequest(BaseModel):
    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )


class ClientSummary(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    client_profile_id: int | None = None
    is_active: bool

    client: ClientSummary | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

    user: UserResponse


class CreateUserRequest(BaseModel):
    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )

    role: UserRole

    client_profile_id: int | None = None


class UpdateUserRequest(BaseModel):
    email: EmailStr | None = None

    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
    )

    role: UserRole | None = None

    client_profile_id: int | None = None

    is_active: bool | None = None