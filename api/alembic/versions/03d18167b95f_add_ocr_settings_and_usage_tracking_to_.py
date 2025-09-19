"""Add OCR settings and usage tracking to AI config

Revision ID: 03d18167b95f
Revises: 873a7fe9e5cd
Create Date: 2025-09-01 09:24:05.818194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03d18167b95f'
down_revision: Union[str, Sequence[str], None] = '873a7fe9e5cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add OCR specific settings
    op.add_column('ai_configs', sa.Column('ocr_enabled', sa.Boolean(), nullable=False, default=False))
    op.add_column('ai_configs', sa.Column('max_tokens', sa.Integer(), nullable=False, default=4096))
    op.add_column('ai_configs', sa.Column('temperature', sa.Float(), nullable=False, default=0.1))

    # Add usage tracking
    op.add_column('ai_configs', sa.Column('usage_count', sa.Integer(), nullable=False, default=0))
    op.add_column('ai_configs', sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True))

    # Update existing created_at and updated_at to use timezone
    op.alter_column('ai_configs', 'created_at',
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=False)
    op.alter_column('ai_configs', 'updated_at',
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=False)

    # Change api_key to Text for longer keys
    op.alter_column('ai_configs', 'api_key',
                    type_=sa.Text(),
                    existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove usage tracking columns
    op.drop_column('ai_configs', 'usage_count')
    op.drop_column('ai_configs', 'last_used_at')

    # Remove OCR specific settings
    op.drop_column('ai_configs', 'ocr_enabled')
    op.drop_column('ai_configs', 'max_tokens')
    op.drop_column('ai_configs', 'temperature')

    # Revert api_key to String
    op.alter_column('ai_configs', 'api_key',
                    type_=sa.String(),
                    existing_nullable=True)
