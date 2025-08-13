"""add labels array column to expenses and backfill from label

Revision ID: add_expense_labels_array_001
Revises: add_expense_label_column_001
Create Date: 2025-08-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_expense_labels_array_001'
down_revision: Union[str, Sequence[str], None] = 'add_expense_label_column_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if 'expenses' not in tables:
        return

    existing_cols = {c['name'] for c in inspector.get_columns('expenses')}
    if 'labels' not in existing_cols:
        op.add_column('expenses', sa.Column('labels', sa.JSON(), nullable=True))
        # Backfill simple label -> labels array
        try:
            op.execute("UPDATE expenses SET labels = CASE WHEN label IS NOT NULL AND label <> '' THEN to_jsonb(ARRAY[label]) ELSE NULL END")
        except Exception:
            pass


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if 'expenses' not in tables:
        return
    existing_cols = {c['name'] for c in inspector.get_columns('expenses')}
    if 'labels' in existing_cols:
        op.drop_column('expenses', 'labels')


