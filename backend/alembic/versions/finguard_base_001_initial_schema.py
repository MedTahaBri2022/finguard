"""initial FinGuard base schema

Revision ID: finguard_base_001
Revises:
Create Date: 2026-09-08

This migration represents the original FinGuard schema
that existed before the first historical Alembic migration.

It intentionally creates only:
- transactions
- analyses
- findings
- alerts

Later migrations are responsible for:
- client_profiles
- analysis tenant linkage
- client_baselines
- users/authentication
- alert tenant linkage
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "finguard_base_001"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = None

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:
    # ========================================================
    # TRANSACTIONS
    # ========================================================

    op.create_table(
        "transactions",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "transaction_id",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "amount",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "category",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "description",
            sa.String(length=500),
            nullable=True,
        ),

        sa.Column(
            "status",
            sa.String(length=50),
            nullable=True,
        ),

        sa.Column(
            "customer",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "transaction_date",
            sa.DateTime(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "id",
        ),

        sa.UniqueConstraint(
            "transaction_id",
            name="uq_transactions_transaction_id",
        ),
    )

    op.create_index(
        op.f("ix_transactions_id"),
        "transactions",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_transactions_transaction_id"),
        "transactions",
        ["transaction_id"],
        unique=True,
    )

    # ========================================================
    # ANALYSES
    # ========================================================
    #
    # Important:
    # client_profile_id is NOT created here.
    #
    # Revision 342373b1e396 adds it later.
    # ========================================================

    op.create_table(
        "analyses",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "filename",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "rows",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "columns",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "risk_score",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "risk_level",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "total_findings",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "high_risk",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "medium_risk",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "low_risk",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "money_at_risk",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "ai_summary",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "id",
        ),
    )

    op.create_index(
        op.f("ix_analyses_id"),
        "analyses",
        ["id"],
        unique=False,
    )

    # ========================================================
    # FINDINGS
    # ========================================================

    op.create_table(
        "findings",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "analysis_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "type",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "severity",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "message",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "amount_at_risk",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "transaction_id",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["analyses.id"],
            name="fk_findings_analysis_id",
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id",
        ),
    )

    op.create_index(
        op.f("ix_findings_id"),
        "findings",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_findings_analysis_id"),
        "findings",
        ["analysis_id"],
        unique=False,
    )

    # ========================================================
    # ALERTS
    # ========================================================
    #
    # Important:
    # analysis_id and client_profile_id are NOT created here.
    #
    # Revision b728cb57a3dc adds those columns later.
    # ========================================================

    op.create_table(
        "alerts",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "alert_type",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "severity",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "message",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "amount_at_risk",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "transaction_id",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "is_read",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "id",
        ),
    )

    op.create_index(
        op.f("ix_alerts_id"),
        "alerts",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    # ========================================================
    # ALERTS
    # ========================================================

    op.drop_index(
        op.f("ix_alerts_id"),
        table_name="alerts",
    )

    op.drop_table(
        "alerts",
    )

    # ========================================================
    # FINDINGS
    # ========================================================

    op.drop_index(
        op.f("ix_findings_analysis_id"),
        table_name="findings",
    )

    op.drop_index(
        op.f("ix_findings_id"),
        table_name="findings",
    )

    op.drop_table(
        "findings",
    )

    # ========================================================
    # ANALYSES
    # ========================================================

    op.drop_index(
        op.f("ix_analyses_id"),
        table_name="analyses",
    )

    op.drop_table(
        "analyses",
    )

    # ========================================================
    # TRANSACTIONS
    # ========================================================

    op.drop_index(
        op.f("ix_transactions_transaction_id"),
        table_name="transactions",
    )

    op.drop_index(
        op.f("ix_transactions_id"),
        table_name="transactions",
    )

    op.drop_table(
        "transactions",
    )