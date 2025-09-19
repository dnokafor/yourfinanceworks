"""Add invoice usage tracking tables

Revision ID: a8251418a34c
Revises: 03d18167b95f
Create Date: 2025-09-01 13:53:46.479041

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8251418a34c'
down_revision: Union[str, Sequence[str], None] = '03d18167b95f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if tables already exist (created manually)
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Create invoice_usage table if it doesn't exist
    if 'invoice_usage' not in inspector.get_table_names():
        op.create_table('invoice_usage',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('tenant_id', sa.Integer(), nullable=True),
            sa.Column('invoice_id', sa.Integer(), nullable=True),
            sa.Column('user_email', sa.String(length=255), nullable=True),
            sa.Column('action', sa.String(length=50), nullable=True),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('previous_status', sa.String(length=50), nullable=True),
            sa.Column('new_status', sa.String(length=50), nullable=True),
            sa.Column('time_spent_ms', sa.Integer(), nullable=True),
            sa.Column('changes_count', sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_invoice_usage_action'), 'invoice_usage', ['action'], unique=False)
        op.create_index(op.f('ix_invoice_usage_id'), 'invoice_usage', ['id'], unique=False)
        op.create_index(op.f('ix_invoice_usage_invoice_id'), 'invoice_usage', ['invoice_id'], unique=False)
        op.create_index(op.f('ix_invoice_usage_tenant_id'), 'invoice_usage', ['tenant_id'], unique=False)
        op.create_index(op.f('ix_invoice_usage_timestamp'), 'invoice_usage', ['timestamp'], unique=False)
        op.create_index(op.f('ix_invoice_usage_user_email'), 'invoice_usage', ['user_email'], unique=False)

    # Create invoice_metrics table if it doesn't exist
    if 'invoice_metrics' not in inspector.get_table_names():
        op.create_table('invoice_metrics',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('tenant_id', sa.Integer(), nullable=True),
            sa.Column('invoice_id', sa.Integer(), nullable=True),
            sa.Column('view_count', sa.Integer(), nullable=True),
            sa.Column('unique_viewers', sa.Integer(), nullable=True),
            sa.Column('last_viewed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('edit_count', sa.Integer(), nullable=True),
            sa.Column('last_edited_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('last_edited_by', sa.String(length=255), nullable=True),
            sa.Column('created_by', sa.String(length=255), nullable=True),
            sa.Column('creation_time_ms', sa.Integer(), nullable=True),
            sa.Column('time_to_first_view', sa.Integer(), nullable=True),
            sa.Column('time_to_payment', sa.Integer(), nullable=True),
            sa.Column('payment_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('status_change_count', sa.Integer(), nullable=True),
            sa.Column('last_status_change', sa.DateTime(timezone=True), nullable=True),
            sa.Column('clone_count', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_invoice_metrics_id'), 'invoice_metrics', ['id'], unique=False)
        op.create_index(op.f('ix_invoice_metrics_invoice_id'), 'invoice_metrics', ['invoice_id'], unique=True)
        op.create_index(op.f('ix_invoice_metrics_tenant_id'), 'invoice_metrics', ['tenant_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Check if tables exist before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Drop invoice_metrics table if it exists
    if 'invoice_metrics' in inspector.get_table_names():
        op.drop_index(op.f('ix_invoice_metrics_tenant_id'), table_name='invoice_metrics')
        op.drop_index(op.f('ix_invoice_metrics_invoice_id'), table_name='invoice_metrics')
        op.drop_index(op.f('ix_invoice_metrics_id'), table_name='invoice_metrics')
        op.drop_table('invoice_metrics')

    # Drop invoice_usage table if it exists
    if 'invoice_usage' in inspector.get_table_names():
        op.drop_index(op.f('ix_invoice_usage_user_email'), table_name='invoice_usage')
        op.drop_index(op.f('ix_invoice_usage_timestamp'), table_name='invoice_usage')
        op.drop_index(op.f('ix_invoice_usage_tenant_id'), table_name='invoice_usage')
        op.drop_index(op.f('ix_invoice_usage_invoice_id'), table_name='invoice_usage')
        op.drop_index(op.f('ix_invoice_usage_id'), table_name='invoice_usage')
        op.drop_index(op.f('ix_invoice_usage_action'), table_name='invoice_usage')
        op.drop_table('invoice_usage')
