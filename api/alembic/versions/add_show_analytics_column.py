"""add show_analytics column to master_users

Revision ID: add_show_analytics_001
Revises: 
Create Date: 2025-08-03 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_show_analytics_001'
down_revision = '2b1a_must_reset_password_master'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if master_users table exists (only in master database)
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'master_users' in inspector.get_table_names():
        columns = inspector.get_columns('master_users')
        column_names = {col['name'] for col in columns}
        
        if 'show_analytics' not in column_names:
            # Add show_analytics column to master_users table
            op.add_column('master_users', sa.Column('show_analytics', sa.Boolean(), nullable=True, default=False))
            
            # Update existing records to have default value
            op.execute("UPDATE master_users SET show_analytics = false WHERE show_analytics IS NULL")
            
            # Make the column non-nullable after setting default values
            op.alter_column('master_users', 'show_analytics', nullable=False)
        else:
            # If the column exists but is nullable, enforce non-nullable for consistency
            show_analytics_col = next((c for c in columns if c['name'] == 'show_analytics'), None)
            if show_analytics_col and show_analytics_col.get('nullable', True):
                op.execute("UPDATE master_users SET show_analytics = false WHERE show_analytics IS NULL")
                op.alter_column('master_users', 'show_analytics', nullable=False)


def downgrade() -> None:
    # Check if master_users table exists (only in master database)
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'master_users' in inspector.get_table_names():
        columns = {col['name'] for col in inspector.get_columns('master_users')}
        if 'show_analytics' in columns:
            # Remove show_analytics column from master_users table
            op.drop_column('master_users', 'show_analytics')