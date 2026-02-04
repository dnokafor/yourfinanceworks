"""Add timeliness_bonus to point_history table

Revision ID: 002_add_timeliness_bonus
Revises: 001_add_gamification_tables
Create Date: 2024-12-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_timeliness_bonus'
down_revision = '001_gamification'
branch_labels = None
depends_on = None


def upgrade():
    """Add timeliness_bonus column to point_history table"""
    op.add_column('point_history', sa.Column('timeliness_bonus', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    """Remove timeliness_bonus column from point_history table"""
    op.drop_column('point_history', 'timeliness_bonus')