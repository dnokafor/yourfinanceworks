"""Merge migration heads

Revision ID: c9d955fdb70c
Revises: 20250122_nullable_reminder, add_database_encryption_support
Create Date: 2025-10-26 22:42:58.470074

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d955fdb70c'
down_revision: Union[str, Sequence[str], None] = ('20250122_nullable_reminder', 'add_database_encryption_support')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
