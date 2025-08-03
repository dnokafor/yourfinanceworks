"""add show_analytics column to master_users

Revision ID: add_show_analytics_001
Revises: 
Create Date: 2025-08-03 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_show_analytics_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add show_analytics column to master_users table
    op.add_column('master_users', sa.Column('show_analytics', sa.Boolean(), nullable=True, default=False))
    
    # Update existing records to have default value
    op.execute("UPDATE master_users SET show_analytics = false WHERE show_analytics IS NULL")
    
    # Make the column non-nullable after setting default values
    op.alter_column('master_users', 'show_analytics', nullable=False)


def downgrade() -> None:
    # Remove show_analytics column from master_users table
    op.drop_column('master_users', 'show_analytics')