"""Add tenant_id column to investment tables

Revision ID: 005_add_tenant_id
Revises: 004_fix_holdings_constraints
Create Date: 2024-01-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_add_tenant_id'
down_revision = '004_fix_holdings_constraints'
branch_labels = None
depends_on = None

def upgrade():
    """Add tenant_id column to investment_portfolios table"""

    # Add tenant_id column to investment_portfolios table
    op.add_column('investment_portfolios', sa.Column('tenant_id', sa.Integer(), nullable=False, server_default='1'))

    # Create index for tenant_id
    op.create_index('ix_investment_portfolios_tenant_id', 'investment_portfolios', ['tenant_id'])

    # Remove server default after adding the column
    op.alter_column('investment_portfolios', 'tenant_id', server_default=None)


def downgrade():
    """Remove tenant_id column from investment_portfolios table"""

    # Drop index first
    op.drop_index('ix_investment_portfolios_tenant_id', 'investment_portfolios')

    # Drop tenant_id column
    op.drop_column('investment_portfolios', 'tenant_id')