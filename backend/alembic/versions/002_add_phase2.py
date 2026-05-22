"""Phase 2A/2B/2C — Add vulnerability_findings, screenshots, secret severity

Revision ID: 002_add_phase2
Revises: 001_initial
Create Date: 2026-05-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '002_add_phase2'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── vulnerability_findings ─────────────────────────────────────────────────
    op.create_table(
        'vulnerability_findings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('template_id', sa.String(), nullable=False),
        sa.Column('template_name', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('host', sa.String(), nullable=False),
        sa.Column('matched_at', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('remediation', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_vuln_findings_scan_id', 'vulnerability_findings', ['scan_id'])
    op.create_index('ix_vuln_findings_severity', 'vulnerability_findings', ['severity'])

    # ── Add screenshot_path to subdomains ──────────────────────────────────────
    op.add_column('subdomains', sa.Column('screenshot_path', sa.String(), nullable=True))

    # ── Add severity + confidence to secrets ───────────────────────────────────
    op.add_column('secrets', sa.Column('severity', sa.String(), nullable=True))
    op.add_column('secrets', sa.Column('confidence', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('secrets', 'confidence')
    op.drop_column('secrets', 'severity')
    op.drop_column('subdomains', 'screenshot_path')
    op.drop_index('ix_vuln_findings_severity', table_name='vulnerability_findings')
    op.drop_index('ix_vuln_findings_scan_id', table_name='vulnerability_findings')
    op.drop_table('vulnerability_findings')
