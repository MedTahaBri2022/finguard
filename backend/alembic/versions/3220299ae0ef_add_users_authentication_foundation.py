"""add users authentication foundation"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f31429ac772"
down_revision: Union[str, None] = "5ac78b4b3aac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "role",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "client_profile_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["client_profile_id"],
            ["client_profiles.id"],
            ondelete="SET NULL",
        ),

        sa.PrimaryKeyConstraint(
            "id",
        ),

        sa.UniqueConstraint(
            "email",
        ),
    )

    op.create_index(
        op.f("ix_users_id"),
        "users",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_users_email"),
        "users",
        ["email"],
        unique=True,
    )

    op.create_index(
        op.f("ix_users_role"),
        "users",
        ["role"],
        unique=False,
    )

    op.create_index(
        op.f("ix_users_client_profile_id"),
        "users",
        ["client_profile_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_users_client_profile_id"),
        table_name="users",
    )

    op.drop_index(
        op.f("ix_users_role"),
        table_name="users",
    )

    op.drop_index(
        op.f("ix_users_email"),
        table_name="users",
    )

    op.drop_index(
        op.f("ix_users_id"),
        table_name="users",
    )

    op.drop_table(
        "users",
    )