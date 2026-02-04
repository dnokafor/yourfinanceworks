"""Fix holdings constraints for closed holdings

Revision ID: 004_fix_holdings_constraints
Revises: 003_investment_tables
Create Date: 2026-02-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_fix_holdings_constraints'
down_revision = '003_investment_tables'
branch_labels = None
depends_on = None

def upgrade():
    """Fix holdings constraints to allow zero cost_basis for closed holdings"""

    # Drop the existing constraint that requires cost_basis > 0
    op.drop_constraint('ck_investment_holdings_positive_cost_basis', 'investment_holdings', type_='check')

    # Add new constraint that allows cost_basis = 0 only when is_closed = true
    op.create_check_constraint(
        'ck_investment_holdings_cost_basis_check',
        'investment_holdings',
        'cost_basis > 0 OR (cost_basis >= 0 AND is_closed = true)'
    )

    # Also update the quantity constraint to allow zero quantity for closed holdings
    op.drop_constraint('ck_investment_holdings_positive_quantity', 'investment_holdings', type_='check')
    op.create_check_constraint(
        'ck_investment_holdings_quantity_check',
        'investment_holdings',
        'quantity > 0 OR (quantity >= 0 AND is_closed = true)'
    )

def downgrade():
    """Revert to original constraints"""

    # Drop the new constraints
    op.drop_constraint('ck_investment_holdings_cost_basis_check', 'investment_holdings', type_='check')
    op.drop_constraint('ck_investment_holdings_quantity_check', 'investment_holdings', type_='check')

    # Restore original constraints
    op.create_check_constraint(
        'ck_investment_holdings_positive_cost_basis',
        'investment_holdings',
        'cost_basis > 0'
    )
    op.create_check_constraint(
        'ck_investment_holdings_positive_quantity',
        'investment_holdings',
        'quantity > 0'
    )