"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-10
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("preferred_language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "crops",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("display_name_en", sa.String(100), nullable=False),
        sa.Column("display_name_te", sa.String(100), nullable=True),
        sa.Column("display_name_hi", sa.String(100), nullable=True),
    )

    op.create_table(
        "disease_predictions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("crop", sa.String(100), nullable=False),
        sa.Column("image_path", sa.String(500), nullable=False),
        sa.Column("disease", sa.String(150), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("is_fallback_prediction", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_predictions_user_id", "disease_predictions", ["user_id"])
    op.create_index("idx_predictions_created_at", "disease_predictions", ["created_at"])

    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("prediction_id", sa.String(36), sa.ForeignKey("disease_predictions.id"), nullable=False, unique=True),
        sa.Column("treatment", sa.Text, nullable=False),
        sa.Column("fertilizer", sa.Text, nullable=True),
        sa.Column("pesticide_guidance", sa.Text, nullable=True),
        sa.Column("prevention", sa.Text, nullable=True),
        sa.Column("crop_management", sa.Text, nullable=True),
        sa.Column("monitoring_advice", sa.Text, nullable=True),
    )

    op.create_table(
        "weather_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("location", sa.String(255), nullable=False),
        sa.Column("temperature", sa.Float, nullable=True),
        sa.Column("humidity", sa.Float, nullable=True),
        sa.Column("rainfall", sa.Float, nullable=True),
        sa.Column("condition", sa.String(100), nullable=True),
        sa.Column("forecast_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_weather_user_id", "weather_records", ["user_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("conversation_id", sa.String(36), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_chat_user_id", "chat_messages", ["user_id"])
    op.create_index("idx_chat_conversation_id", "chat_messages", ["conversation_id"])

    op.create_table(
        "reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("prediction_id", sa.String(36), sa.ForeignKey("disease_predictions.id"), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_reports_user_id", "reports", ["user_id"])


def downgrade():
    op.drop_table("reports")
    op.drop_table("chat_messages")
    op.drop_table("weather_records")
    op.drop_table("recommendations")
    op.drop_table("disease_predictions")
    op.drop_table("crops")
    op.drop_table("users")
