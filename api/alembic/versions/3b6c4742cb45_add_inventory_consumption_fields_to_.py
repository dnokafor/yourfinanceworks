"""Add inventory consumption fields to expenses table

Revision ID: 3b6c4742cb45
Revises: 9ccd38ec0098
Create Date: 2025-09-16 02:26:39.188318

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b6c4742cb45'
down_revision: Union[str, Sequence[str], None] = '9ccd38ec0098'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add inventory consumption fields to expenses table
    op.add_column('expenses', sa.Column('is_inventory_consumption', sa.Boolean(), nullable=False, default=False))
    op.add_column('expenses', sa.Column('consumption_items', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove inventory consumption fields from expenses table
    op.drop_column('expenses', 'consumption_items')
    op.drop_column('expenses', 'is_inventory_consumption')
