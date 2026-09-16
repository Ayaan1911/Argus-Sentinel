"""add scan is_demo flag

Revision ID: c7f0a3d9e21b
Revises: 9429a108190d
Create Date: 2026-09-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7f0a3d9e21b'
down_revision = '9429a108190d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'scans',
        sa.Column('is_demo', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column('scans', 'is_demo')
