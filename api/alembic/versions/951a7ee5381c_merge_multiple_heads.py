"""merge_multiple_heads

Revision ID: 951a7ee5381c
Revises: add_analytics_table, add_show_analytics_001
Create Date: 2025-08-06 02:45:54.996759

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '951a7ee5381c'
down_revision: Union[str, Sequence[str], None] = ('add_analytics_table', 'add_show_analytics_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
