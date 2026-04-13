"""001 - Initial schema

Revision ID: 001_initial
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Analysis Tasks table
    op.create_table(
        "analysis_tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "parsing", "sanitizing", "enriching",
                "llm_analysis", "completed", "failed",
                name="taskstatus",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("progress_stage", sa.String(50), server_default="QUEUED"),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("log_format", sa.String(20), nullable=True),
        sa.Column("line_count", sa.Integer(), nullable=True),
        sa.Column("sampled", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Analysis Reports table
    op.create_table(
        "analysis_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "task_id", UUID(as_uuid=True),
            sa.ForeignKey("analysis_tasks.id", ondelete="CASCADE"),
            nullable=False, unique=True,
        ),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("incidents", JSON, server_default="[]"),
        sa.Column("waf_suggestions", JSON, server_default="[]"),
        sa.Column("llm_provider", sa.String(20), nullable=True),
        sa.Column("llm_model", sa.String(50), nullable=True),
        sa.Column("token_usage", JSON, nullable=True),
        sa.Column("processing_time_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index("ix_tasks_status", "analysis_tasks", ["status"])
    op.create_index("ix_tasks_created", "analysis_tasks", ["created_at"])
    op.create_index("ix_tasks_file_hash", "analysis_tasks", ["file_hash"])


def downgrade():
    op.drop_table("analysis_reports")
    op.drop_table("analysis_tasks")
    op.execute("DROP TYPE IF EXISTS taskstatus")
