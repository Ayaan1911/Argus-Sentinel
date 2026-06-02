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
    op.add_column('secrets', sa.Column('validated', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('secrets', sa.Column('validation_proof', sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column('secrets', 'validation_proof')
    op.drop_column('secrets', 'validated')
