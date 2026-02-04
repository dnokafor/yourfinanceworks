"""
Integration tests for Investment Holdings Repository

This module tests the HoldingsRepository with a real database session
to ensure proper functionality and data persistence.
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from plugins.investments.models import (
    InvestmentHolding, InvestmentPortfolio, SecurityType, AssetClass, PortfolioType,
    Base as InvestmentBase
)
from plugins.investments.repositories.holdings_repository import HoldingsRepository
from plugins.investments.repositories.portfolio_repository import PortfolioRepository


class TestHoldingsRepositoryIntegration:
    """Integration test suite for HoldingsRepository"""

    @pytest.fixture
    def investment_db_session(self):
        """Create an in-memory SQLite database session for investment testing"""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )

        # Create investment tables
        InvestmentBase.metadata.create_all(bind=engine)

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()

        try:
            yield session
        finally:
            session.close()

    @pytest.fixture
    def holdings_repository(self, investment_db_session):
        """Create a HoldingsRepository instance with test database session"""
        return HoldingsRepository(investment_db_session)

    @pytest.fixture
    def portfolio_repository(self, investment_db_session):
        """Create a PortfolioRepository instance with test database session"""
        return PortfolioRepository(investment_db_session)

    @pytest.fixture
    def sample_portfolio(self, portfolio_repository):
        """Create a sample portfolio for testing"""
        return portfolio_repository.create(
            name="Test Portfolio",
            portfolio_type=PortfolioType.TAXABLE
        )

    def test_create_holding_success(self, holdings_repository, sample_portfolio):
        """Test successful holding creation with real database"""
        # Arrange
        security_symbol = "AAPL"
        security_name = "Apple Inc."
        security_type = SecurityType.STOCK
        asset_class = AssetClass.STOCKS
        quantity = Decimal('100')
        cost_basis = Decimal('15000.00')
        purchase_date = date(2024, 1, 15)

        # Act
        holding = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol=security_symbol,
            security_name=security_name,
            security_type=security_type,
            asset_class=asset_class,
            quantity=quantity,
            cost_basis=cost_basis,
            purchase_date=purchase_date
        )

        # Assert
        assert holding is not None
        assert holding.id is not None
        assert holding.portfolio_id == sample_portfolio.id
        assert holding.security_symbol == security_symbol
        assert holding.security_name == security_name
        assert holding.security_type == security_type
        assert holding.asset_class == asset_class
        assert holding.quantity == quantity
        assert holding.cost_basis == cost_basis
        assert holding.purchase_date == purchase_date
        assert holding.is_closed == False
        assert holding.created_at is not None
        assert holding.updated_at is not None

    def test_get_by_id_success(self, holdings_repository, sample_portfolio):
        """Test retrieving holding by ID"""
        # Arrange
        created_holding = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="MSFT",
            security_name="Microsoft Corp.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('50'),
            cost_basis=Decimal('10000.00'),
            purchase_date=date(2024, 1, 10)
        )

        # Act
        retrieved_holding = holdings_repository.get_by_id(created_holding.id)

        # Assert
        assert retrieved_holding is not None
        assert retrieved_holding.id == created_holding.id
        assert retrieved_holding.security_symbol == "MSFT"
        assert retrieved_holding.quantity == Decimal('50')

    def test_get_by_portfolio(self, holdings_repository, sample_portfolio):
        """Test retrieving holdings by portfolio"""
        # Arrange
        holding1 = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="AAPL",
            security_name="Apple Inc.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('100'),
            cost_basis=Decimal('15000.00'),
            purchase_date=date(2024, 1, 15)
        )

        holding2 = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="GOOGL",
            security_name="Alphabet Inc.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('25'),
            cost_basis=Decimal('7500.00'),
            purchase_date=date(2024, 1, 20)
        )

        # Act
        holdings = holdings_repository.get_by_portfolio(sample_portfolio.id)

        # Assert
        assert len(holdings) == 2
        symbols = [h.security_symbol for h in holdings]
        assert "AAPL" in symbols
        assert "GOOGL" in symbols

    def test_update_holding(self, holdings_repository, sample_portfolio):
        """Test updating a holding"""
        # Arrange
        holding = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="TSLA",
            security_name="Tesla Inc.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('10'),
            cost_basis=Decimal('8000.00'),
            purchase_date=date(2024, 1, 25)
        )

        # Act
        updated_holding = holdings_repository.update(
            holding.id,
            quantity=Decimal('15'),
            current_price=Decimal('850.00')
        )

        # Assert
        assert updated_holding is not None
        assert updated_holding.quantity == Decimal('15')
        assert updated_holding.current_price == Decimal('850.00')

    def test_update_price(self, holdings_repository, sample_portfolio):
        """Test updating holding price"""
        # Arrange
        holding = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="NVDA",
            security_name="NVIDIA Corp.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('20'),
            cost_basis=Decimal('12000.00'),
            purchase_date=date(2024, 1, 30)
        )

        # Act
        updated_holding = holdings_repository.update_price(holding.id, Decimal('650.00'))

        # Assert
        assert updated_holding is not None
        assert updated_holding.current_price == Decimal('650.00')
        assert updated_holding.price_updated_at is not None

    def test_adjust_quantity_buy(self, holdings_repository, sample_portfolio):
        """Test adjusting quantity for buy transaction"""
        # Arrange
        holding = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="AMD",
            security_name="Advanced Micro Devices",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('100'),
            cost_basis=Decimal('15000.00'),
            purchase_date=date(2024, 2, 1)
        )

        # Act
        updated_holding = holdings_repository.adjust_quantity(
            holding.id,
            quantity_delta=Decimal('50'),
            cost_delta=Decimal('8000.00')
        )

        # Assert
        assert updated_holding is not None
        assert updated_holding.quantity == Decimal('150')
        assert updated_holding.cost_basis == Decimal('23000.00')

    def test_adjust_quantity_sell(self, holdings_repository, sample_portfolio):
        """Test adjusting quantity for sell transaction"""
        # Arrange
        holding = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="INTC",
            security_name="Intel Corp.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('200'),
            cost_basis=Decimal('10000.00'),
            purchase_date=date(2024, 2, 5)
        )

        # Act
        updated_holding = holdings_repository.adjust_quantity(
            holding.id,
            quantity_delta=Decimal('-50'),
            cost_delta=Decimal('-2500.00')
        )

        # Assert
        assert updated_holding is not None
        assert updated_holding.quantity == Decimal('150')
        assert updated_holding.cost_basis == Decimal('7500.00')

    def test_adjust_quantity_insufficient_shares(self, holdings_repository, sample_portfolio):
        """Test adjusting quantity with insufficient shares raises error"""
        # Arrange
        holding = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="META",
            security_name="Meta Platforms",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('50'),
            cost_basis=Decimal('15000.00'),
            purchase_date=date(2024, 2, 10)
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Insufficient quantity"):
            holdings_repository.adjust_quantity(
                holding.id,
                quantity_delta=Decimal('-100'),  # Try to sell more than we have
                cost_delta=Decimal('-30000.00')
            )

    def test_close_holding(self, holdings_repository, sample_portfolio):
        """Test closing a holding"""
        # Arrange
        holding = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="NFLX",
            security_name="Netflix Inc.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('25'),
            cost_basis=Decimal('12500.00'),
            purchase_date=date(2024, 2, 15)
        )

        # Act
        closed_holding = holdings_repository.close(holding.id)

        # Assert
        assert closed_holding is not None
        assert closed_holding.is_closed == True

    def test_get_by_symbol(self, holdings_repository, sample_portfolio):
        """Test getting holdings by symbol"""
        # Arrange
        holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="AMZN",
            security_name="Amazon.com Inc.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('30'),
            cost_basis=Decimal('9000.00'),
            purchase_date=date(2024, 2, 20)
        )

        # Act
        holdings = holdings_repository.get_by_symbol(sample_portfolio.id, "AMZN")

        # Assert
        assert len(holdings) == 1
        assert holdings[0].security_symbol == "AMZN"

    def test_get_by_asset_class(self, holdings_repository, sample_portfolio):
        """Test getting holdings by asset class"""
        # Arrange
        holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="VTI",
            security_name="Vanguard Total Stock Market ETF",
            security_type=SecurityType.ETF,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('100'),
            cost_basis=Decimal('25000.00'),
            purchase_date=date(2024, 2, 25)
        )

        holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="BND",
            security_name="Vanguard Total Bond Market ETF",
            security_type=SecurityType.ETF,
            asset_class=AssetClass.BONDS,
            quantity=Decimal('200'),
            cost_basis=Decimal('16000.00'),
            purchase_date=date(2024, 2, 25)
        )

        # Act
        stock_holdings = holdings_repository.get_by_asset_class(sample_portfolio.id, AssetClass.STOCKS)
        bond_holdings = holdings_repository.get_by_asset_class(sample_portfolio.id, AssetClass.BONDS)

        # Assert
        assert len(stock_holdings) == 1
        assert stock_holdings[0].security_symbol == "VTI"
        assert len(bond_holdings) == 1
        assert bond_holdings[0].security_symbol == "BND"

    def test_get_portfolio_value(self, holdings_repository, sample_portfolio):
        """Test calculating portfolio value"""
        # Arrange
        holding1 = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="SPY",
            security_name="SPDR S&P 500 ETF",
            security_type=SecurityType.ETF,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('50'),
            cost_basis=Decimal('20000.00'),
            purchase_date=date(2024, 3, 1)
        )

        holding2 = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="QQQ",
            security_name="Invesco QQQ Trust",
            security_type=SecurityType.ETF,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('25'),
            cost_basis=Decimal('10000.00'),
            purchase_date=date(2024, 3, 1)
        )

        # Update prices
        holdings_repository.update_price(holding1.id, Decimal('450.00'))
        holdings_repository.update_price(holding2.id, Decimal('380.00'))

        # Act
        total_value = holdings_repository.get_portfolio_value(sample_portfolio.id)

        # Assert
        expected_value = (Decimal('50') * Decimal('450.00')) + (Decimal('25') * Decimal('380.00'))
        assert total_value == expected_value  # 22500 + 9500 = 32000

    def test_get_portfolio_cost_basis(self, holdings_repository, sample_portfolio):
        """Test calculating portfolio cost basis"""
        # Arrange
        holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="IWM",
            security_name="iShares Russell 2000 ETF",
            security_type=SecurityType.ETF,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('100'),
            cost_basis=Decimal('18000.00'),
            purchase_date=date(2024, 3, 5)
        )

        holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="EFA",
            security_name="iShares MSCI EAFE ETF",
            security_type=SecurityType.ETF,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('75'),
            cost_basis=Decimal('5250.00'),
            purchase_date=date(2024, 3, 5)
        )

        # Act
        total_cost_basis = holdings_repository.get_portfolio_cost_basis(sample_portfolio.id)

        # Assert
        assert total_cost_basis == Decimal('23250.00')  # 18000 + 5250

    def test_validate_tenant_access(self, holdings_repository, sample_portfolio):
        """Test tenant access validation"""
        # Arrange
        holding = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="DIA",
            security_name="SPDR Dow Jones Industrial Average ETF",
            security_type=SecurityType.ETF,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('30'),
            cost_basis=Decimal('12000.00'),
            purchase_date=date(2024, 3, 10)
        )

        # Act & Assert
        assert holdings_repository.validate_tenant_access(holding.id) == True
        assert holdings_repository.validate_tenant_access(99999) == False

    def test_exists(self, holdings_repository, sample_portfolio):
        """Test checking if holding exists"""
        # Arrange
        holding = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="XLF",
            security_name="Financial Select Sector SPDR Fund",
            security_type=SecurityType.ETF,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('150'),
            cost_basis=Decimal('6000.00'),
            purchase_date=date(2024, 3, 15)
        )

        # Act & Assert
        assert holdings_repository.exists(holding.id) == True
        assert holdings_repository.exists(99999) == False

    def test_count_by_portfolio(self, holdings_repository, sample_portfolio):
        """Test counting holdings by portfolio"""
        # Arrange
        for i in range(3):
            holdings_repository.create(
                portfolio_id=sample_portfolio.id,
                security_symbol=f"TEST{i}",
                security_name=f"Test Security {i}",
                security_type=SecurityType.STOCK,
                asset_class=AssetClass.STOCKS,
                quantity=Decimal('10'),
                cost_basis=Decimal('1000.00'),
                purchase_date=date(2024, 3, 20)
            )

        # Act
        count = holdings_repository.count_by_portfolio(sample_portfolio.id)

        # Assert
        assert count == 3

    def test_get_asset_class_summary(self, holdings_repository, sample_portfolio):
        """Test getting asset class summary"""
        # Arrange
        # Create stock holding
        stock_holding = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="STOCK1",
            security_name="Stock Security",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('100'),
            cost_basis=Decimal('10000.00'),
            purchase_date=date(2024, 3, 25)
        )

        # Create bond holding
        bond_holding = holdings_repository.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="BOND1",
            security_name="Bond Security",
            security_type=SecurityType.BOND,
            asset_class=AssetClass.BONDS,
            quantity=Decimal('200'),
            cost_basis=Decimal('20000.00'),
            purchase_date=date(2024, 3, 25)
        )

        # Update prices
        holdings_repository.update_price(stock_holding.id, Decimal('120.00'))
        holdings_repository.update_price(bond_holding.id, Decimal('95.00'))

        # Act
        summary = holdings_repository.get_asset_class_summary(sample_portfolio.id)

        # Assert
        assert len(summary) == 2

        # Find stocks and bonds in summary
        stocks_summary = next(item for item in summary if item['asset_class'] == AssetClass.STOCKS)
        bonds_summary = next(item for item in summary if item['asset_class'] == AssetClass.BONDS)

        assert stocks_summary['total_value'] == Decimal('12000.00')  # 100 * 120
        assert stocks_summary['holdings_count'] == 1

        assert bonds_summary['total_value'] == Decimal('19000.00')  # 200 * 95
        assert bonds_summary['holdings_count'] == 1