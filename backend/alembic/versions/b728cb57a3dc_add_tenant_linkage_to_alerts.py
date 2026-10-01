"""add tenant linkage to alerts

Revision ID: b728cb57a3dc
Revises: 8f31429ac772
Create Date: 2026-09-04 17:08:31.309956
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b728cb57a3dc"
down_revision: Union[str, Sequence[str], None] = "8f31429ac772"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    with op.batch_alter_table(
        "alerts",
        schema=None,
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "analysis_id",
                sa.Integer(),
                nullable=True,
            )
        )

        batch_op.add_column(
            sa.Column(
                "client_profile_id",
                sa.Integer(),
                nullable=True,
            )
        )

        batch_op.create_index(
            batch_op.f(
                "ix_alerts_analysis_id"
            ),
            ["analysis_id"],
            unique=False,
        )

        batch_op.create_index(
            batch_op.f(
                "ix_alerts_client_profile_id"
            ),
            ["client_profile_id"],
            unique=False,
        )

        batch_op.create_foreign_key(
            "fk_alerts_analysis_id_analyses",
            "analyses",
            ["analysis_id"],
            ["id"],
            ondelete="CASCADE",
        )

        batch_op.create_foreign_key(
            "fk_alerts_client_profile_id_client_profiles",
            "client_profiles",
            ["client_profile_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    """Downgrade schema."""

    with op.batch_alter_table(
        "alerts",
        schema=None,
    ) as batch_op:

        batch_op.drop_constraint(
            "fk_alerts_client_profile_id_client_profiles",
            type_="foreignkey",
        )

        batch_op.drop_constraint(
            "fk_alerts_analysis_id_analyses",
            type_="foreignkey",
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_alerts_client_profile_id"
            )
        )

        batch_op.drop_index(
            batch_op.f(
                "ix_alerts_analysis_id"
            )
        )

        batch_op.drop_column(
            "client_profile_id"
        )

        batch_op.drop_column(
            "analysis_id"
        )