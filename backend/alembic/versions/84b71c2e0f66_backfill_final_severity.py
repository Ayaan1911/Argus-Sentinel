"""Backfill severity and business impact from the final correlated score.

Revision ID: 84b71c2e0f66
Revises: c7f0a3d9e21b
"""
from alembic import op
import sqlalchemy as sa


revision = "84b71c2e0f66"
down_revision = "c7f0a3d9e21b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    findings = sa.table(
        "findings",
        sa.column("final_risk_score", sa.Float),
        sa.column("severity", sa.String),
        sa.column("business_impact", sa.Text),
    )
    score = findings.c.final_risk_score
    op.execute(findings.update().values(
        severity=sa.case(
            (score > 8, "critical"),
            (score > 6, "high"),
            (score > 4, "medium"),
            (score > 2, "low"),
            else_="informational",
        ),
        business_impact=sa.case(
            (score > 6, "Significant business risk"),
            (score > 4, "Moderate business risk"),
            else_="Minimal business risk",
        ),
    ))


def downgrade() -> None:
    # Prior labels were derived from pre-correlation scores; the incorrect
    # values cannot be reconstructed after backfill.
    pass
