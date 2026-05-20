"""Initial migration — create all tables

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# Alembic revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── scans ──────────────────────────────────────────────────────────────────
    op.create_table(
        'scans',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('domain', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('current_stage', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── subdomains ─────────────────────────────────────────────────────────────
    op.create_table(
        'subdomains',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('subdomain', sa.String(), nullable=False),
        sa.Column('is_alive', sa.Boolean(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('technologies', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── ports ──────────────────────────────────────────────────────────────────
    op.create_table(
        'ports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('subdomain_id', sa.Integer(), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('protocol', sa.String(), nullable=True),
        sa.Column('service', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['subdomain_id'], ['subdomains.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── secrets ────────────────────────────────────────────────────────────────
    op.create_table(
        'secrets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('file_url', sa.String(), nullable=False),
        sa.Column('secret_type', sa.String(), nullable=False),
        sa.Column('matched_value', sa.String(), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── endpoints ──────────────────────────────────────────────────────────────
    op.create_table(
        'endpoints',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('source_file', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── takeover_risks ─────────────────────────────────────────────────────────
    op.create_table(
        'takeover_risks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('subdomain', sa.String(), nullable=False),
        sa.Column('cname', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('fingerprint', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── ai_summaries ───────────────────────────────────────────────────────────
    op.create_table(
        'ai_summaries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('scan_id'),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── indexes ────────────────────────────────────────────────────────────────
    op.create_index('ix_subdomains_scan_id', 'subdomains', ['scan_id'])
    op.create_index('ix_secrets_scan_id', 'secrets', ['scan_id'])
    op.create_index('ix_endpoints_scan_id', 'endpoints', ['scan_id'])
    op.create_index('ix_takeover_risks_scan_id', 'takeover_risks', ['scan_id'])
    op.create_index('ix_scans_status', 'scans', ['status'])


def downgrade() -> None:
    op.drop_index('ix_scans_status', table_name='scans')
    op.drop_index('ix_takeover_risks_scan_id', table_name='takeover_risks')
    op.drop_index('ix_endpoints_scan_id', table_name='endpoints')
    op.drop_index('ix_secrets_scan_id', table_name='secrets')
    op.drop_index('ix_subdomains_scan_id', table_name='subdomains')
    op.drop_table('ai_summaries')
    op.drop_table('takeover_risks')
    op.drop_table('endpoints')
    op.drop_table('secrets')
    op.drop_table('ports')
    op.drop_table('subdomains')
    op.drop_table('scans')
