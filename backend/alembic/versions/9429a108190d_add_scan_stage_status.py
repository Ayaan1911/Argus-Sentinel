"""add scan stage_status

Revision ID: 9429a108190d
Revises: 5da69c924778
Create Date: 2026-09-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '9429a108190d'
down_revision = '5da69c924778'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'scans',
        sa.Column('stage_status', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
    )


def downgrade() -> None:
    op.drop_column('scans', 'stage_status')
