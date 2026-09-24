"""store optional recommendation context on predictions

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "disease_predictions",
        sa.Column("context_json", sa.String(4000), nullable=True),
    )


def downgrade():
    op.drop_column("disease_predictions", "context_json")
