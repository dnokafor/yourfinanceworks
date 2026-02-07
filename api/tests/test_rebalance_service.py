import pytest
from decimal import Decimal
from datetime import date
from plugins.investments.services.rebalance_service import RebalanceService
from plugins.investments.models import AssetClass, SecurityType
from plugins.investments.schemas import PortfolioUpdate, PortfolioCreate, PortfolioType, HoldingCreate

@pytest.fixture
def tenant_id():
    return 1

@pytest.fixture
def rebalance_service(db_session):
    return RebalanceService(db_session)

def test_generate_rebalance_report_no_targets(rebalance_service, investment_portfolio_service, tenant_id):
    # Setup: Create a portfolio without targets
    portfolio = investment_portfolio_service.create_portfolio(
        tenant_id=tenant_id,
        portfolio_data=PortfolioCreate(name="Test Portfolio", portfolio_type=PortfolioType.TAXABLE)
    )

    # Test
    report = rebalance_service.generate_rebalance_report(portfolio.id, tenant_id)

    # Assert
    assert report is None

def test_generate_rebalance_report_with_targets_empty_portfolio(rebalance_service, investment_portfolio_service, tenant_id):
    # Setup: Create a portfolio with targets but no holdings
    portfolio = investment_portfolio_service.create_portfolio(
        tenant_id=tenant_id,
        portfolio_data=PortfolioCreate(name="Test Portfolio", portfolio_type=PortfolioType.TAXABLE)
    )

    targets = {AssetClass.STOCKS: Decimal('60'), AssetClass.BONDS: Decimal('40')}
    investment_portfolio_service.update_portfolio(portfolio.id, tenant_id, PortfolioUpdate(target_allocations=targets))

    # Test
    report = rebalance_service.generate_rebalance_report(portfolio.id, tenant_id)

    # Assert
    assert report is not None
    assert report.total_value == 0
    assert report.is_balanced is True
    assert "Portfolio is empty" in report.summary

def test_generate_rebalance_report_drift(rebalance_service, investment_portfolio_service, investment_holdings_service, tenant_id):
    # Setup: Create a portfolio, add holdings, set targets
    portfolio = investment_portfolio_service.create_portfolio(
        tenant_id=tenant_id,
        portfolio_data=PortfolioCreate(name="Test Portfolio", portfolio_type=PortfolioType.TAXABLE)
    )

    # Add holdings (100% Stocks)
    holding = investment_holdings_service.create_holding(tenant_id, portfolio.id, HoldingCreate(
        security_symbol="AAPL",
        security_name="Apple Inc.",
        security_type=SecurityType.STOCK,
        asset_class=AssetClass.STOCKS,
        quantity=Decimal('10'),
        cost_basis=Decimal('1500'),
        purchase_date=date.today()
    ))

    # Update current price to $200
    investment_holdings_service.update_price(tenant_id, holding.id, Decimal('200'))

    # Set targets (50% Stocks, 50% Bonds)
    targets = {AssetClass.STOCKS: Decimal('50'), AssetClass.BONDS: Decimal('50')}
    investment_portfolio_service.update_portfolio(portfolio.id, tenant_id, PortfolioUpdate(target_allocations=targets))

    # Test
    report = rebalance_service.generate_rebalance_report(portfolio.id, tenant_id)

    # Assert
    assert report is not None
    assert report.total_value == Decimal('2000.0') # 10 * 200
    assert report.current_allocations[AssetClass.STOCKS] == Decimal('100.0')
    assert report.drifts[AssetClass.STOCKS] == Decimal('50.0')
    assert report.drifts[AssetClass.BONDS] == Decimal('-50.0')
    assert not report.is_balanced

    # Check recommendations
    # Sell $1000 Stocks, Buy $1000 Bonds
    sell_action = next(a for a in report.recommended_actions if a.asset_class == AssetClass.STOCKS)
    buy_action = next(a for a in report.recommended_actions if a.asset_class == AssetClass.BONDS)

    assert sell_action.action_type == "SELL"
    assert sell_action.amount == Decimal('1000.0')
    assert buy_action.action_type == "BUY"
    assert buy_action.amount == Decimal('1000.0')
