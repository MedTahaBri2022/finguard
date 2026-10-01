"""link client profile to analyses

Revision ID: 342373b1e396
Revises:
Create Date: 2026-09-01 13:58:44.679910
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "342373b1e396"
down_revision: Union[str, Sequence[str], None] = "finguard_base_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create client_profiles and link analyses to clients.
    """

    # ========================================================
    # CREATE CLIENT PROFILES TABLE
    # ========================================================

    op.create_table(
        "client_profiles",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "business_type",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "base_currency",
            sa.String(length=10),
            nullable=False,
        ),

        sa.Column(
            "risk_tolerance",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "column_mapping_json",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "business_rules_json",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "failure_rate_warning",
            sa.Float(),
            nullable=True,
        ),

        sa.Column(
            "refund_rate_warning",
            sa.Float(),
            nullable=True,
        ),

        sa.Column(
            "high_amount_multiplier",
            sa.Float(),
            nullable=True,
        ),

        sa.Column(
            "baseline_ready",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "minimum_history_rows",
            sa.Integer(),
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

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    # ========================================================
    # CLIENT PROFILE INDEXES
    # ========================================================

    with op.batch_alter_table(
        "client_profiles",
        schema=None,
    ) as batch_op:

        batch_op.create_index(
            batch_op.f(
                "ix_client_profiles_id"
            ),
            ["id"],
            unique=False,
        )

        batch_op.create_index(
            batch_op.f(
                "ix_client_profiles_name"
            ),
            ["name"],
            unique=True,
        )

    # ========================================================
    # LINK ANALYSIS -> CLIENT PROFILE
    # ========================================================

    with op.batch_alter_table(
        "analyses",
        schema=None,
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "client_profile_id",
                sa.Integer(),
                nullable=True,
            )
        )

        batch_op.create_index(
            batch_op.f(
                "ix_analyses_client_profile_id"
            ),
            ["client_profile_id"],
            unique=False,
        )

        batch_op.create_foreign_key(
            "fk_analyses_client_profile_id",
            "client_profiles",
            ["client_profile_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    """
    Remove the ClientProfile relation and table.
    """

    # ========================================================
    # REMOVE ANALYSIS -> CLIENT PROFILE LINK
    # ========================================================

    with op.batch_alter_table(
        "analyses",
        schema=None,
    ) as batch_op:

        batch_op.drop_constraint(
            "fk_analyses_client_profile_id",
            type_="foreignkey",
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_analyses_client_profile_id"
            )
        )

        batch_op.drop_column(
            "client_profile_id"
        )

    # ========================================================
    # REMOVE CLIENT PROFILE INDEXES
    # ========================================================

    with op.batch_alter_table(
        "client_profiles",
        schema=None,
    ) as batch_op:

        batch_op.drop_index(
            batch_op.f(
                "ix_client_profiles_name"
            )
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_client_profiles_id"
            )
        )

    # ========================================================
    # DROP CLIENT PROFILE TABLE
    # ========================================================

    op.drop_table(
        "client_profiles"
    )