"""add client baselines

Revision ID: 5ac78b4b3aac
Revises: 342373b1e396
Create Date: 2026-09-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5ac78b4b3aac"
down_revision: Union[str, Sequence[str], None] = "342373b1e396"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "client_baselines",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "client_profile_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "sample_size",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "baseline_json",
            sa.Text(),
            nullable=False,
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

        sa.ForeignKeyConstraint(
            ["client_profile_id"],
            ["client_profiles.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    with op.batch_alter_table(
        "client_baselines",
        schema=None,
    ) as batch_op:

        batch_op.create_index(
            batch_op.f(
                "ix_client_baselines_client_profile_id"
            ),
            ["client_profile_id"],
            unique=False,
        )

        batch_op.create_index(
            batch_op.f(
                "ix_client_baselines_id"
            ),
            ["id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table(
        "client_baselines",
        schema=None,
    ) as batch_op:

        batch_op.drop_index(
            batch_op.f(
                "ix_client_baselines_id"
            )
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_client_baselines_client_profile_id"
            )
        )

    op.drop_table(
        "client_baselines"
    )