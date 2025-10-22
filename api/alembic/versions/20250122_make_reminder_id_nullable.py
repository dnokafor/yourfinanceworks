"""make reminder_id nullable in reminder_notifications

Revision ID: 20250122_nullable_reminder
Revises: 3db559573430
Create Date: 2025-01-22 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250122_nullable_reminder'
down_revision = '3db559573430'
branch_labels = None
depends_on = None


def upgrade():
    # Make reminder_id nullable to support system notifications like join requests
    op.alter_column('reminder_notifications', 'reminder_id',
                    existing_type=sa.Integer(),
                    nullable=True)


def downgrade():
    # Revert reminder_id to not nullable
    op.alter_column('reminder_notifications', 'reminder_id',
                    existing_type=sa.Integer(),
                    nullable=False)
