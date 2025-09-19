"""add label column to expenses

Revision ID: add_expense_label_column_001
Revises: add_ocr_fields_to_expenses_001
Create Date: 2025-08-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_expense_label_column_001'
down_revision: Union[str, Sequence[str], None] = 'add_ocr_fields_to_expenses_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if 'expenses' not in tables:
        return

    existing_cols = {c['name'] for c in inspector.get_columns('expenses')}
    if 'label' not in existing_cols:
        op.add_column('expenses', sa.Column('label', sa.String(length=255), nullable=True))
        try:
            op.create_index('ix_expenses_label', 'expenses', ['label'], unique=False)
        except Exception:
            pass


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if 'expenses' not in tables:
        return
    try:
        op.drop_index('ix_expenses_label', table_name='expenses')
    except Exception:
        pass
    existing_cols = {c['name'] for c in inspector.get_columns('expenses')}
    if 'label' in existing_cols:
        op.drop_column('expenses', 'label')


