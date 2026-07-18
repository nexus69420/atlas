"""create deployments table

Revision ID: 20260719_0007
Revises: 20260718_0006
Create Date: 2026-07-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260719_0007"
down_revision: str | None = "20260718_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "deployments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("model_key", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("artifact_key", sa.String(length=1024), nullable=False),
        sa.Column("bundle_key", sa.String(length=1024), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("prediction_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["experiment_id"], ["experiments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_deployments_project_id"), "deployments", ["project_id"], unique=False
    )
    op.create_index(
        op.f("ix_deployments_experiment_id"),
        "deployments",
        ["experiment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_deployments_experiment_id"), table_name="deployments")
    op.drop_index(op.f("ix_deployments_project_id"), table_name="deployments")
    op.drop_table("deployments")
