"""Merge multiple heads

Revision ID: 873a7fe9e5cd
Revises: add_bank_txn_invoice_link_001, fix_bank_txn_fk_constraints_001
Create Date: 2025-09-01 09:23:49.545513

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '873a7fe9e5cd'
down_revision: Union[str, Sequence[str], None] = ('add_bank_txn_invoice_link_001', 'fix_bank_txn_fk_constraints_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
