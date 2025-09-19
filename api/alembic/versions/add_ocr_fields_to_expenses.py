"""add OCR fields to expenses

Revision ID: add_ocr_fields_to_expenses_001
Revises: add_expense_invoice_link_001
Create Date: 2025-08-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_ocr_fields_to_expenses_001'
down_revision: Union[str, Sequence[str], None] = 'add_expense_invoice_link_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if 'expenses' not in tables:
        return

    existing_cols = {c['name'] for c in inspector.get_columns('expenses')}

    if 'imported_from_attachment' not in existing_cols:
        op.add_column('expenses', sa.Column('imported_from_attachment', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')))
        op.execute("ALTER TABLE expenses ALTER COLUMN imported_from_attachment DROP DEFAULT")
    if 'analysis_status' not in existing_cols:
        op.add_column('expenses', sa.Column('analysis_status', sa.String(length=50), nullable=False, server_default='not_started'))
        op.execute("ALTER TABLE expenses ALTER COLUMN analysis_status DROP DEFAULT")
    if 'analysis_result' not in existing_cols:
        op.add_column('expenses', sa.Column('analysis_result', sa.JSON(), nullable=True))
    if 'analysis_error' not in existing_cols:
        op.add_column('expenses', sa.Column('analysis_error', sa.Text(), nullable=True))
    if 'manual_override' not in existing_cols:
        op.add_column('expenses', sa.Column('manual_override', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')))
        op.execute("ALTER TABLE expenses ALTER COLUMN manual_override DROP DEFAULT")
    if 'analysis_updated_at' not in existing_cols:
        op.add_column('expenses', sa.Column('analysis_updated_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if 'expenses' not in tables:
        return
    existing_cols = {c['name'] for c in inspector.get_columns('expenses')}

    if 'analysis_updated_at' in existing_cols:
        op.drop_column('expenses', 'analysis_updated_at')
    if 'manual_override' in existing_cols:
        op.drop_column('expenses', 'manual_override')
    if 'analysis_error' in existing_cols:
        op.drop_column('expenses', 'analysis_error')
    if 'analysis_result' in existing_cols:
        op.drop_column('expenses', 'analysis_result')
    if 'analysis_status' in existing_cols:
        op.drop_column('expenses', 'analysis_status')
    if 'imported_from_attachment' in existing_cols:
        op.drop_column('expenses', 'imported_from_attachment')


