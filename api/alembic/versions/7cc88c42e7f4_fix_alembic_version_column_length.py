"""fix alembic version column length

Revision ID: 7cc88c42e7f4
Revises: a8251418a34c
Create Date: 2025-09-07 23:54:17.239355

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7cc88c42e7f4'
down_revision: Union[str, Sequence[str], None] = 'a8251418a34c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix alembic_version table column length to accommodate longer revision IDs."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Check if alembic_version table exists
    if 'alembic_version' in inspector.get_table_names():
        # Get current column info
        columns = inspector.get_columns('alembic_version')
        version_col = next((c for c in columns if c['name'] == 'version_num'), None)
        
        if version_col:
            # Check if column needs to be expanded (if it's less than 128 chars)
            current_length = version_col.get('type').length if hasattr(version_col.get('type'), 'length') else None
            if current_length and current_length < 128:
                # Expand the column to accommodate longer revision IDs
                op.alter_column('alembic_version', 'version_num', 
                              type_=sa.String(128),
                              existing_type=sa.String(current_length))


def downgrade() -> None:
    """Revert alembic_version column length back to original size."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Check if alembic_version table exists
    if 'alembic_version' in inspector.get_table_names():
        # Revert back to original length (32)
        op.alter_column('alembic_version', 'version_num',
                       type_=sa.String(32),
                       existing_type=sa.String(128))
