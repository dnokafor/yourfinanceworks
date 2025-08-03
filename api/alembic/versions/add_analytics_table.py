"""Add analytics table

Revision ID: add_analytics_table
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_analytics_table'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create page_views table in master database
    op.create_table('page_views',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('path', sa.String(length=500), nullable=True),
        sa.Column('method', sa.String(length=10), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_page_views_id'), 'page_views', ['id'], unique=False)
    op.create_index(op.f('ix_page_views_user_email'), 'page_views', ['user_email'], unique=False)
    op.create_index(op.f('ix_page_views_tenant_id'), 'page_views', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_page_views_path'), 'page_views', ['path'], unique=False)
    op.create_index(op.f('ix_page_views_timestamp'), 'page_views', ['timestamp'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_page_views_timestamp'), table_name='page_views')
    op.drop_index(op.f('ix_page_views_path'), table_name='page_views')
    op.drop_index(op.f('ix_page_views_tenant_id'), table_name='page_views')
    op.drop_index(op.f('ix_page_views_user_email'), table_name='page_views')
    op.drop_index(op.f('ix_page_views_id'), table_name='page_views')
    op.drop_table('page_views')