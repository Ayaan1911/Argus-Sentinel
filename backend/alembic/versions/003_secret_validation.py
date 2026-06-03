"""Add secret validation columns

Revision ID: 003_secret_validation
Revises: 002_add_phase2
Create Date: 2026-06-02 21:20:06.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '003_secret_validation'
down_revision = '002_add_phase2'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # ── Add validated + validation_proof to secrets ─────────────────────────────
    op.execute("ALTER TABLE secrets ADD COLUMN IF NOT EXISTS validated BOOLEAN DEFAULT FALSE")
    op.execute("ALTER TABLE secrets ADD COLUMN IF NOT EXISTS validation_proof TEXT")

def downgrade() -> None:
    op.execute("ALTER TABLE secrets DROP COLUMN IF EXISTS validation_proof")
    op.execute("ALTER TABLE secrets DROP COLUMN IF EXISTS validated")
