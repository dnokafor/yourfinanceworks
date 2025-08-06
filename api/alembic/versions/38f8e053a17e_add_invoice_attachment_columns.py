"""add_invoice_attachment_columns

Revision ID: 38f8e053a17e
Revises: 467164d8d5af
Create Date: 2025-08-06 03:09:26.870331

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38f8e053a17e'
down_revision: Union[str, Sequence[str], None] = '467164d8d5af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add attachment columns to invoices table
    op.add_column('invoices', sa.Column('attachment_path', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('attachment_filename', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove attachment columns from invoices table
    op.drop_column('invoices', 'attachment_filename')
    op.drop_column('invoices', 'attachment_path')
