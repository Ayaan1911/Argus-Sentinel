"""Create the original scans and findings tables.

Revision ID: 5da69c924778
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "5da69c924778"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("target", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("audience", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_scans_id", "scans", ["id"])
    op.create_index("ix_scans_target", "scans", ["target"])
    op.create_table(
        "findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scans.id"), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("raw_data", postgresql.JSONB()),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("technical_impact", sa.Text()),
        sa.Column("business_impact", sa.Text()),
        sa.Column("attack_patterns", postgresql.JSONB()),
        sa.Column("recommended_actions", postgresql.JSONB()),
        sa.Column("learning_resources", postgresql.JSONB()),
        sa.Column("related_findings", postgresql.JSONB()),
        sa.Column("audience_guidance", postgresql.JSONB()),
        sa.Column("reasoning_breakdown", postgresql.JSONB()),
        sa.Column("correlation_modifier", sa.Float()),
        sa.Column("final_risk_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_findings_id", "findings", ["id"])


def downgrade() -> None:
    op.drop_index("ix_findings_id", table_name="findings")
    op.drop_table("findings")
    op.drop_index("ix_scans_target", table_name="scans")
    op.drop_index("ix_scans_id", table_name="scans")
    op.drop_table("scans")
