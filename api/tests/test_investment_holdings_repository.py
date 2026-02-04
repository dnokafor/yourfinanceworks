"""
Unit tests for Investment Holdings Repository

This module tests the HoldingsRepository class to ensure proper CRUD operations,
tenant isolation, and data integrity for investment holdings.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timezone
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from plugins.investments.repositories.holdings_repository import HoldingsRepository
from plugins.investments.models import (
    InvestmentHolding, InvestmentPortfolio, SecurityType, AssetClass, PortfolioType
)


class TestHoldingsRepository:
    """Test cases for HoldingsRepository"""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def holdings_repo(self, mock_db_session):
        """Create a HoldingsRepository instance with mock session"""
        return HoldingsRepository(db_session=mock_db_session)

    @pytest.fixture
    def sample_portfolio(self):
        """Create a sample portfolio for testing"""
        return InvestmentPortfolio(
            id=1,
            name="Test Portfolio",
            portfolio_type=PortfolioType.TAXABLE,
            is_archived=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    @pytest.fixture
    def sample_holding(self, sample_portfolio):
        """Create a sample holding for testing"""
        return InvestmentHolding(
            id=1,
            portfolio_id=sample_portfolio.id,
            security_symbol="AAPL",
            security_name="Apple Inc.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('100'),
            cost_basis=Decimal('15000.00'),
            purchase_date=date(2024, 1, 15),
            current_price=Decimal('175.00'),
            price_updated_at=datetime.now(timezone.utc),
            is_closed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    def test_create_holding_success(self, holdings_repo, mock_db_session):
        """Test successful holding creation"""
        # Arrange
        portfolio_id = 1
        security_symbol = "AAPL"
        security_name = "Apple Inc."
        security_type = SecurityType.STOCK
        asset_class = AssetClass.STOCKS
        quantity = Decimal('100')
        cost_basis = Decimal('15000.00')
        purchase_date = date(2024, 1, 15)

        # Act
        result = holdings_repo.create(
            portfolio_id=portfolio_id,
            security_symbol=security_symbol,
            security_name=security_name,
            security_type=security_type,
            asset_class=asset_class,
            quantity=quantity,
            cost_basis=cost_basis,
            purchase_date=purchase_date
        )

        # Assert
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

        # Verify the holding was created with correct attributes
        added_holding = mock_db_session.add.call_args[0][0]
        assert added_holding.portfolio_id == portfolio_id
        assert added_holding.security_symbol == security_symbol
        assert added_holding.security_name == security_name
        assert added_holding.security_type == security_type
        assert added_holding.asset_class == asset_class
        assert added_holding.quantity == quantity
        assert added_holding.cost_basis == cost_basis
        assert added_holding.purchase_date == purchase_date
        assert added_holding.is_closed == False

    def test_get_by_id_found(self, holdings_repo, mock_db_session, sample_holding):
        """Test getting holding by ID when it exists"""
        # Arrange
        holding_id = 1
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_holding

        # Act
        result = holdings_repo.get_by_id(holding_id)

        # Assert
        assert result == sample_holding
        mock_db_session.query.assert_called_once_with(InvestmentHolding)

    def test_get_by_id_not_found(self, holdings_repo, mock_db_session):
        """Test getting holding by ID when it doesn't exist"""
        # Arrange
        holding_id = 999
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Act
        result = holdings_repo.get_by_id(holding_id)

        # Assert
        assert result is None

    def test_get_by_portfolio_active_only(self, holdings_repo, mock_db_session, sample_holding):
        """Test getting holdings by portfolio (active only)"""
        # Arrange
        portfolio_id = 1
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_holding]

        # Act
        result = holdings_repo.get_by_portfolio(portfolio_id, include_closed=False)

        # Assert
        assert result == [sample_holding]
        mock_db_session.query.assert_called_once_with(InvestmentHolding)

    def test_get_by_portfolio_include_closed(self, holdings_repo, mock_db_session, sample_holding):
        """Test getting holdings by portfolio including closed holdings"""
        # Arrange
        portfolio_id = 1
        closed_holding = InvestmentHolding(
            id=2,
            portfolio_id=portfolio_id,
            security_symbol="MSFT",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('0'),
            cost_basis=Decimal('0'),
            purchase_date=date(2024, 1, 1),
            is_closed=True
        )

        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_holding, closed_holding]

        # Act
        result = holdings_repo.get_by_portfolio(portfolio_id, include_closed=True)

        # Assert
        assert len(result) == 2
        assert sample_holding in result
        assert closed_holding in result

    def test_update_holding_success(self, holdings_repo, mock_db_session, sample_holding):
        """Test successful holding update"""
        # Arrange
        holding_id = 1
        updates = {
            'security_name': 'Apple Inc. Updated',
            'quantity': Decimal('150'),
            'current_price': Decimal('180.00')
        }

        # Mock get_by_id to return the sample holding
        holdings_repo.get_by_id = Mock(return_value=sample_holding)

        # Act
        result = holdings_repo.update(holding_id, **updates)

        # Assert
        assert result == sample_holding
        assert sample_holding.security_name == 'Apple Inc. Updated'
        assert sample_holding.quantity == Decimal('150')
        assert sample_holding.current_price == Decimal('180.00')
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(sample_holding)

    def test_update_holding_not_found(self, holdings_repo, mock_db_session):
        """Test updating non-existent holding"""
        # Arrange
        holding_id = 999
        updates = {'quantity': Decimal('150')}

        # Mock get_by_id to return None
        holdings_repo.get_by_id = Mock(return_value=None)

        # Act
        result = holdings_repo.update(holding_id, **updates)

        # Assert
        assert result is None
        mock_db_session.commit.assert_not_called()

    def test_update_holding_auto_close_on_zero_quantity(self, holdings_repo, mock_db_session, sample_holding):
        """Test that holding is auto-closed when quantity reaches zero"""
        # Arrange
        holding_id = 1
        updates = {'quantity': Decimal('0')}

        # Mock get_by_id to return the sample holding
        holdings_repo.get_by_id = Mock(return_value=sample_holding)

        # Act
        result = holdings_repo.update(holding_id, **updates)

        # Assert
        assert result == sample_holding
        assert sample_holding.quantity == Decimal('0')
        assert sample_holding.is_closed == True

    def test_update_price_success(self, holdings_repo, mock_db_session, sample_holding):
        """Test successful price update"""
        # Arrange
        holding_id = 1
        new_price = Decimal('185.00')

        # Mock the update method
        holdings_repo.update = Mock(return_value=sample_holding)

        # Act
        result = holdings_repo.update_price(holding_id, new_price)

        # Assert
        assert result == sample_holding
        holdings_repo.update.assert_called_once()
        call_args = holdings_repo.update.call_args
        assert call_args[0][0] == holding_id
        assert call_args[1]['current_price'] == new_price
        assert 'price_updated_at' in call_args[1]

    def test_adjust_quantity_buy_transaction(self, holdings_repo, mock_db_session, sample_holding):
        """Test adjusting quantity for a buy transaction"""
        # Arrange
        holding_id = 1
        quantity_delta = Decimal('50')  # Buy 50 more shares
        cost_delta = Decimal('9000.00')  # Cost $9000

        # Mock get_by_id to return the sample holding
        holdings_repo.get_by_id = Mock(return_value=sample_holding)
        holdings_repo.update = Mock(return_value=sample_holding)

        # Act
        result = holdings_repo.adjust_quantity(holding_id, quantity_delta, cost_delta)

        # Assert
        holdings_repo.update.assert_called_once_with(
            holding_id,
            quantity=Decimal('150'),  # 100 + 50
            cost_basis=Decimal('24000.00')  # 15000 + 9000
        )

    def test_adjust_quantity_sell_transaction(self, holdings_repo, mock_db_session, sample_holding):
        """Test adjusting quantity for a sell transaction"""
        # Arrange
        holding_id = 1
        quantity_delta = Decimal('-30')  # Sell 30 shares
        cost_delta = Decimal('-4500.00')  # Reduce cost basis

        # Mock get_by_id to return the sample holding
        holdings_repo.get_by_id = Mock(return_value=sample_holding)
        holdings_repo.update = Mock(return_value=sample_holding)

        # Act
        result = holdings_repo.adjust_quantity(holding_id, quantity_delta, cost_delta)

        # Assert
        holdings_repo.update.assert_called_once_with(
            holding_id,
            quantity=Decimal('70'),  # 100 - 30
            cost_basis=Decimal('10500.00')  # 15000 - 4500
        )

    def test_adjust_quantity_insufficient_quantity(self, holdings_repo, mock_db_session, sample_holding):
        """Test adjusting quantity with insufficient shares"""
        # Arrange
        holding_id = 1
        quantity_delta = Decimal('-150')  # Try to sell 150 shares (only have 100)
        cost_delta = Decimal('-15000.00')

        # Mock get_by_id to return the sample holding
        holdings_repo.get_by_id = Mock(return_value=sample_holding)

        # Act & Assert
        with pytest.raises(ValueError, match="Insufficient quantity"):
            holdings_repo.adjust_quantity(holding_id, quantity_delta, cost_delta)

    def test_adjust_quantity_negative_cost_basis(self, holdings_repo, mock_db_session, sample_holding):
        """Test adjusting quantity with cost basis going too negative"""
        # Arrange
        holding_id = 1
        quantity_delta = Decimal('-50')
        cost_delta = Decimal('-20000.00')  # Would make cost basis negative

        # Mock get_by_id to return the sample holding
        holdings_repo.get_by_id = Mock(return_value=sample_holding)

        # Act & Assert
        with pytest.raises(ValueError, match="Cost basis cannot be negative"):
            holdings_repo.adjust_quantity(holding_id, quantity_delta, cost_delta)

    def test_close_holding(self, holdings_repo, mock_db_session, sample_holding):
        """Test closing a holding"""
        # Arrange
        holding_id = 1
        holdings_repo.update = Mock(return_value=sample_holding)

        # Act
        result = holdings_repo.close(holding_id)

        # Assert
        holdings_repo.update.assert_called_once_with(holding_id, is_closed=True)
        assert result == sample_holding

    def test_get_by_symbol(self, holdings_repo, mock_db_session, sample_holding):
        """Test getting holdings by symbol"""
        # Arrange
        portfolio_id = 1
        security_symbol = "AAPL"

        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_holding]

        # Act
        result = holdings_repo.get_by_symbol(portfolio_id, security_symbol)

        # Assert
        assert result == [sample_holding]

    def test_get_by_asset_class(self, holdings_repo, mock_db_session, sample_holding):
        """Test getting holdings by asset class"""
        # Arrange
        portfolio_id = 1
        asset_class = AssetClass.STOCKS

        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_holding]

        # Act
        result = holdings_repo.get_by_asset_class(portfolio_id, asset_class)

        # Assert
        assert result == [sample_holding]

    def test_get_by_security_type(self, holdings_repo, mock_db_session, sample_holding):
        """Test getting holdings by security type"""
        # Arrange
        portfolio_id = 1
        security_type = SecurityType.STOCK

        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_holding]

        # Act
        result = holdings_repo.get_by_security_type(portfolio_id, security_type)

        # Assert
        assert result == [sample_holding]

    def test_get_portfolio_value(self, holdings_repo, mock_db_session, sample_holding):
        """Test calculating portfolio value"""
        # Arrange
        portfolio_id = 1
        holdings_repo.get_by_portfolio = Mock(return_value=[sample_holding])

        # Act
        result = holdings_repo.get_portfolio_value(portfolio_id)

        # Assert
        expected_value = sample_holding.current_value  # 100 * 175.00 = 17500.00
        assert result == expected_value

    def test_get_portfolio_cost_basis(self, holdings_repo, mock_db_session):
        """Test calculating portfolio cost basis"""
        # Arrange
        portfolio_id = 1
        expected_cost_basis = Decimal('15000.00')

        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = expected_cost_basis

        # Act
        result = holdings_repo.get_portfolio_cost_basis(portfolio_id)

        # Assert
        assert result == expected_cost_basis

    def test_validate_tenant_access_valid(self, holdings_repo, mock_db_session, sample_holding):
        """Test tenant access validation for valid holding"""
        # Arrange
        holding_id = 1
        holdings_repo.get_by_id = Mock(return_value=sample_holding)

        # Act
        result = holdings_repo.validate_tenant_access(holding_id)

        # Assert
        assert result == True

    def test_validate_tenant_access_invalid(self, holdings_repo, mock_db_session):
        """Test tenant access validation for invalid holding"""
        # Arrange
        holding_id = 999
        holdings_repo.get_by_id = Mock(return_value=None)

        # Act
        result = holdings_repo.validate_tenant_access(holding_id)

        # Assert
        assert result == False

    def test_exists_true(self, holdings_repo, mock_db_session):
        """Test exists method returns True for existing holding"""
        # Arrange
        holding_id = 1

        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = Mock()  # Non-None result

        # Act
        result = holdings_repo.exists(holding_id)

        # Assert
        assert result == True

    def test_exists_false(self, holdings_repo, mock_db_session):
        """Test exists method returns False for non-existing holding"""
        # Arrange
        holding_id = 999

        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Act
        result = holdings_repo.exists(holding_id)

        # Assert
        assert result == False

    def test_count_by_portfolio(self, holdings_repo, mock_db_session):
        """Test counting holdings by portfolio"""
        # Arrange
        portfolio_id = 1
        expected_count = 3

        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = expected_count

        # Act
        result = holdings_repo.count_by_portfolio(portfolio_id)

        # Assert
        assert result == expected_count

    def test_get_asset_class_summary(self, holdings_repo, mock_db_session):
        """Test getting asset class summary"""
        # Arrange
        portfolio_id = 1

        # Create holdings with different asset classes
        stock_holding = InvestmentHolding(
            id=1,
            portfolio_id=portfolio_id,
            security_symbol="AAPL",
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('100'),
            cost_basis=Decimal('15000'),
            current_price=Decimal('175'),
            purchase_date=date(2024, 1, 1)
        )

        bond_holding = InvestmentHolding(
            id=2,
            portfolio_id=portfolio_id,
            security_symbol="BND",
            asset_class=AssetClass.BONDS,
            quantity=Decimal('200'),
            cost_basis=Decimal('20000'),
            current_price=Decimal('85'),
            purchase_date=date(2024, 1, 1)
        )

        holdings_repo.get_by_portfolio = Mock(return_value=[stock_holding, bond_holding])

        # Act
        result = holdings_repo.get_asset_class_summary(portfolio_id)

        # Assert
        assert len(result) == 2

        # Find stocks and bonds in result
        stocks_summary = next(item for item in result if item['asset_class'] == AssetClass.STOCKS)
        bonds_summary = next(item for item in result if item['asset_class'] == AssetClass.BONDS)

        assert stocks_summary['total_value'] == Decimal('17500')  # 100 * 175
        assert stocks_summary['holdings_count'] == 1

        assert bonds_summary['total_value'] == Decimal('17000')  # 200 * 85
        assert bonds_summary['holdings_count'] == 1

    def test_close_session(self, holdings_repo, mock_db_session):
        """Test closing database session"""
        # Act
        holdings_repo.close_session()

        # Assert
        mock_db_session.close.assert_called_once()