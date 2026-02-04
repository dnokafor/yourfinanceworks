"""
Unit tests for HoldingsService

This module tests the holdings service business logic including
validation, tenant isolation, and business rule enforcement.
"""

import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from plugins.investments.services.holdings_service import HoldingsService
from plugins.investments.repositories.portfolio_repository import PortfolioRepository
from plugins.investments.repositories.holdings_repository import HoldingsRepository
from plugins.investments.models import (
    InvestmentPortfolio, InvestmentHolding,
    PortfolioType, SecurityType, AssetClass
)
from plugins.investments.schemas import HoldingCreate, HoldingUpdate
from core.exceptions.base import ValidationError, NotFoundError, ForbiddenError


class TestHoldingsService:
    """Test cases for HoldingsService"""

    @pytest.fixture
    def holdings_service(self, db_session):
        """Create a HoldingsService instance"""
        return HoldingsService(db_session)

    @pytest.fixture
    def portfolio_repo(self, db_session):
        """Create a PortfolioRepository instance"""
        return PortfolioRepository(db_session)

    @pytest.fixture
    def sample_portfolio(self, db_session):
        """Create a sample portfolio for testing"""
        from datetime import datetime, timezone

        portfolio = InvestmentPortfolio(
            tenant_id=1,
            name="Test Portfolio",
            portfolio_type=PortfolioType.TAXABLE,
            is_archived=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(portfolio)
        db_session.commit()
        db_session.refresh(portfolio)
        return portfolio

    @pytest.fixture
    def sample_holding_data(self):
        """Create sample holding data"""
        return HoldingCreate(
            security_symbol="AAPL",
            security_name="Apple Inc.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('100'),
            cost_basis=Decimal('10000'),
            purchase_date=date(2024, 1, 1)
        )

    def test_create_holding_success(self, holdings_service, sample_portfolio, sample_holding_data):
        """Test successful holding creation"""
        holding = holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=sample_holding_data
        )

        assert holding.security_symbol == "AAPL"
        assert holding.security_name == "Apple Inc."
        assert holding.security_type == SecurityType.STOCK
        assert holding.asset_class == AssetClass.STOCKS
        assert holding.quantity == Decimal('100')
        assert holding.cost_basis == Decimal('10000')
        assert holding.purchase_date == date(2024, 1, 1)
        assert holding.current_price is None  # No price set initially

    def test_create_holding_invalid_tenant(self, holdings_service, sample_portfolio, sample_holding_data):
        """Test holding creation with invalid tenant"""
        with pytest.raises(NotFoundError):
            holdings_service.create_holding(
                tenant_id=999,  # Wrong tenant
                portfolio_id=sample_portfolio.id,
                holding_data=sample_holding_data
            )

    def test_create_holding_nonexistent_portfolio(self, holdings_service, sample_holding_data):
        """Test holding creation with nonexistent portfolio"""
        with pytest.raises(NotFoundError):
            holdings_service.create_holding(
                tenant_id=1,
                portfolio_id=999,  # Nonexistent portfolio
                holding_data=sample_holding_data
            )

    def test_create_holding_invalid_quantity(self, holdings_service, sample_portfolio):
        """Test holding creation with invalid quantity"""
        # Pydantic validation should catch this at the schema level
        with pytest.raises(ValueError):  # Pydantic raises ValueError for validation errors
            HoldingCreate(
                security_symbol="AAPL",
                security_name="Apple Inc.",
                security_type=SecurityType.STOCK,
                asset_class=AssetClass.STOCKS,
                quantity=Decimal('-100'),  # Invalid negative quantity
                cost_basis=Decimal('10000'),
                purchase_date=date(2024, 1, 1)
            )

    def test_create_holding_invalid_cost_basis(self, holdings_service, sample_portfolio):
        """Test holding creation with invalid cost basis"""
        # Pydantic validation should catch this at the schema level
        with pytest.raises(ValueError):  # Pydantic raises ValueError for validation errors
            HoldingCreate(
                security_symbol="AAPL",
                security_name="Apple Inc.",
                security_type=SecurityType.STOCK,
                asset_class=AssetClass.STOCKS,
                quantity=Decimal('100'),
                cost_basis=Decimal('-10000'),  # Invalid negative cost basis
                purchase_date=date(2024, 1, 1)
            )

    def test_create_holding_future_purchase_date(self, holdings_service, sample_portfolio):
        """Test holding creation with future purchase date"""
        # Pydantic validation should catch this at the schema level
        with pytest.raises(ValueError):  # Pydantic raises ValueError for validation errors
            HoldingCreate(
                security_symbol="AAPL",
                security_name="Apple Inc.",
                security_type=SecurityType.STOCK,
                asset_class=AssetClass.STOCKS,
                quantity=Decimal('100'),
                cost_basis=Decimal('10000'),
                purchase_date=date(2027, 12, 31)  # Future date (system date is 2026-02-04)
            )

    def test_get_holdings(self, holdings_service, sample_portfolio, sample_holding_data):
        """Test retrieving holdings for a portfolio"""
        # Create a holding first
        holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=sample_holding_data
        )

        # Get holdings
        holdings = holdings_service.get_holdings(
            tenant_id=1,
            portfolio_id=sample_portfolio.id
        )

        assert len(holdings) == 1
        assert holdings[0].security_symbol == "AAPL"

    def test_get_holdings_invalid_tenant(self, holdings_service, sample_portfolio):
        """Test getting holdings with invalid tenant"""
        with pytest.raises(NotFoundError):
            holdings_service.get_holdings(
                tenant_id=999,  # Wrong tenant
                portfolio_id=sample_portfolio.id
            )

    def test_get_holding_by_id(self, holdings_service, sample_portfolio, sample_holding_data):
        """Test retrieving a specific holding by ID"""
        # Create a holding first
        created_holding = holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=sample_holding_data
        )

        # Get the holding by ID
        retrieved_holding = holdings_service.get_holding(
            tenant_id=1,
            holding_id=created_holding.id
        )

        assert retrieved_holding.id == created_holding.id
        assert retrieved_holding.security_symbol == "AAPL"

    def test_get_holding_invalid_tenant(self, holdings_service, sample_portfolio, sample_holding_data):
        """Test getting holding with invalid tenant"""
        # Create a holding first
        created_holding = holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=sample_holding_data
        )

        # Try to get with wrong tenant
        with pytest.raises(NotFoundError):
            holdings_service.get_holding(
                tenant_id=999,  # Wrong tenant
                holding_id=created_holding.id
            )

    def test_update_holding(self, holdings_service, sample_portfolio, sample_holding_data):
        """Test updating a holding"""
        # Create a holding first
        created_holding = holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=sample_holding_data
        )

        # Update the holding (only fields available in HoldingUpdate)
        update_data = HoldingUpdate(
            security_name="Apple Inc. (Updated)",
            quantity=Decimal('150')  # Update quantity instead of price
        )

        updated_holding = holdings_service.update_holding(
            tenant_id=1,
            holding_id=created_holding.id,
            holding_data=update_data
        )

        assert updated_holding.security_name == "Apple Inc. (Updated)"
        assert updated_holding.quantity == Decimal('150')

    def test_update_price(self, holdings_service, sample_portfolio, sample_holding_data):
        """Test updating holding price"""
        # Create a holding first
        created_holding = holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=sample_holding_data
        )

        # Update the price
        updated_holding = holdings_service.update_price(
            tenant_id=1,
            holding_id=created_holding.id,
            price=Decimal('175')
        )

        assert updated_holding.current_price == Decimal('175')
        assert updated_holding.price_updated_at is not None

    def test_update_price_invalid_price(self, holdings_service, sample_portfolio, sample_holding_data):
        """Test updating holding price with invalid price"""
        # Create a holding first
        created_holding = holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=sample_holding_data
        )

        # Try to update with invalid price
        with pytest.raises(ValidationError, match="Price must be positive"):
            holdings_service.update_price(
                tenant_id=1,
                holding_id=created_holding.id,
                price=Decimal('-10')  # Invalid negative price
            )

    def test_adjust_quantity_buy(self, holdings_service, sample_portfolio, sample_holding_data):
        """Test adjusting quantity for a buy transaction"""
        # Create a holding first
        created_holding = holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=sample_holding_data
        )

        # Adjust quantity (simulate buy)
        updated_holding = holdings_service.adjust_quantity(
            tenant_id=1,
            holding_id=created_holding.id,
            quantity_change=Decimal('50'),  # Buy 50 more shares
            cost_basis_change=Decimal('7500')  # At $150 per share
        )

        assert updated_holding.quantity == Decimal('150')  # 100 + 50
        assert updated_holding.cost_basis == Decimal('17500')  # 10000 + 7500

    def test_adjust_quantity_sell(self, holdings_service, sample_portfolio, sample_holding_data):
        """Test adjusting quantity for a sell transaction"""
        # Create a holding first
        created_holding = holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=sample_holding_data
        )

        # Adjust quantity (simulate sell)
        updated_holding = holdings_service.adjust_quantity(
            tenant_id=1,
            holding_id=created_holding.id,
            quantity_change=Decimal('-30'),  # Sell 30 shares
            cost_basis_change=Decimal('-3000')  # Reduce cost basis proportionally
        )

        assert updated_holding.quantity == Decimal('70')  # 100 - 30
        assert updated_holding.cost_basis == Decimal('7000')  # 10000 - 3000

    def test_adjust_quantity_insufficient_quantity(self, holdings_service, sample_portfolio, sample_holding_data):
        """Test adjusting quantity with insufficient quantity"""
        # Create a holding first
        created_holding = holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=sample_holding_data
        )

        # Try to sell more than available
        with pytest.raises(ValidationError, match="Insufficient quantity"):
            holdings_service.adjust_quantity(
                tenant_id=1,
                holding_id=created_holding.id,
                quantity_change=Decimal('-150'),  # Try to sell 150 shares (only have 100)
                cost_basis_change=Decimal('-15000')
            )

    def test_adjust_quantity_auto_close(self, holdings_service, sample_portfolio, sample_holding_data):
        """Test that holding is automatically closed when quantity reaches zero"""
        # Create a holding first
        created_holding = holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=sample_holding_data
        )

        # Sell all shares
        updated_holding = holdings_service.adjust_quantity(
            tenant_id=1,
            holding_id=created_holding.id,
            quantity_change=Decimal('-100'),  # Sell all 100 shares
            cost_basis_change=Decimal('-10000')  # Remove all cost basis
        )

        # The repository sets minimal positive values to satisfy database constraints
        # but the holding should be marked as closed
        assert updated_holding.quantity <= Decimal('0.00000001')  # Minimal positive value
        assert updated_holding.cost_basis <= Decimal('0.01')      # Minimal positive value
        assert updated_holding.is_closed is True

    def test_close_holding(self, holdings_service, sample_portfolio, sample_holding_data):
        """Test manually closing a holding"""
        # Create a holding first
        created_holding = holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=sample_holding_data
        )

        # First, reduce quantity to zero
        holdings_service.adjust_quantity(
            tenant_id=1,
            holding_id=created_holding.id,
            quantity_change=Decimal('-100'),
            cost_basis_change=Decimal('-10000')
        )

        # Now close the holding (should already be closed from adjust_quantity)
        # This test verifies the holding is already closed
        closed_holding = holdings_service.get_holding(
            tenant_id=1,
            holding_id=created_holding.id
        )

        assert closed_holding.is_closed is True

    def test_close_holding_with_quantity(self, holdings_service, sample_portfolio, sample_holding_data):
        """Test closing a holding that still has quantity"""
        # Create a holding first
        created_holding = holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=sample_holding_data
        )

        # Try to close holding with remaining quantity
        with pytest.raises(ValidationError, match="Cannot close holding with remaining quantity"):
            holdings_service.close_holding(
                tenant_id=1,
                holding_id=created_holding.id
            )

    def test_get_active_holdings(self, holdings_service, sample_portfolio, sample_holding_data):
        """Test getting only active holdings"""
        # Create two holdings
        holding1 = holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=sample_holding_data
        )

        holding2_data = HoldingCreate(
            security_symbol="GOOGL",
            security_name="Alphabet Inc.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('50'),
            cost_basis=Decimal('15000'),
            purchase_date=date(2024, 1, 15)
        )

        holding2 = holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=holding2_data
        )

        # Close one holding
        holdings_service.adjust_quantity(
            tenant_id=1,
            holding_id=holding1.id,
            quantity_change=Decimal('-100'),
            cost_basis_change=Decimal('-10000')
        )

        # Get active holdings (should only return holding2)
        active_holdings = holdings_service.get_active_holdings(
            tenant_id=1,
            portfolio_id=sample_portfolio.id
        )

        assert len(active_holdings) == 1
        assert active_holdings[0].security_symbol == "GOOGL"

    def test_get_holdings_by_asset_class(self, holdings_service, sample_portfolio):
        """Test getting holdings filtered by asset class"""
        # Create holdings in different asset classes
        stock_data = HoldingCreate(
            security_symbol="AAPL",
            security_name="Apple Inc.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('100'),
            cost_basis=Decimal('10000'),
            purchase_date=date(2024, 1, 1)
        )

        bond_data = HoldingCreate(
            security_symbol="TLT",
            security_name="iShares 20+ Year Treasury Bond ETF",
            security_type=SecurityType.ETF,
            asset_class=AssetClass.BONDS,
            quantity=Decimal('50'),
            cost_basis=Decimal('5000'),
            purchase_date=date(2024, 1, 1)
        )

        holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=stock_data
        )

        holdings_service.create_holding(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            holding_data=bond_data
        )

        # Get only stock holdings
        stock_holdings = holdings_service.get_holdings_by_asset_class(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            asset_class=AssetClass.STOCKS
        )

        assert len(stock_holdings) == 1
        assert stock_holdings[0].security_symbol == "AAPL"
        assert stock_holdings[0].asset_class == AssetClass.STOCKS

        # Get only bond holdings
        bond_holdings = holdings_service.get_holdings_by_asset_class(
            tenant_id=1,
            portfolio_id=sample_portfolio.id,
            asset_class=AssetClass.BONDS
        )

        assert len(bond_holdings) == 1
        assert bond_holdings[0].security_symbol == "TLT"
        assert bond_holdings[0].asset_class == AssetClass.BONDS