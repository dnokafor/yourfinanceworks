"""
Unit tests for Investment Portfolio Service

This module tests the PortfolioService class to ensure proper business logic,
validation, and integration with repositories.
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone
from decimal import Decimal

# Import investment models and service
from plugins.investments.models import (
    InvestmentPortfolio,
    InvestmentHolding,
    PortfolioType,
    SecurityType,
    AssetClass,
    Base as InvestmentBase
)
from plugins.investments.services.portfolio_service import PortfolioService
from plugins.investments.schemas import PortfolioCreate, PortfolioUpdate


class TestPortfolioService:
    """Test suite for PortfolioService"""

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
    def portfolio_service(self, investment_db_session):
        """Create a PortfolioService instance with test database session"""
        return PortfolioService(investment_db_session)

    @pytest.fixture
    def sample_portfolio_data(self):
        """Sample portfolio creation data"""
        return PortfolioCreate(
            name="Test Portfolio",
            portfolio_type=PortfolioType.TAXABLE
        )

    def test_create_portfolio_success(self, portfolio_service, sample_portfolio_data):
        """Test successful portfolio creation"""
        # Arrange
        tenant_id = 1

        # Act
        portfolio = portfolio_service.create_portfolio(tenant_id, sample_portfolio_data)

        # Assert
        assert portfolio is not None
        assert portfolio.name == "Test Portfolio"
        assert portfolio.portfolio_type == PortfolioType.TAXABLE
        assert portfolio.is_archived == False
        assert portfolio.id is not None

    def test_create_portfolio_with_empty_name_raises_error(self, portfolio_service):
        """Test that creating portfolio with empty name raises ValueError"""
        # Arrange
        tenant_id = 1
        portfolio_data = PortfolioCreate(
            name="   ",  # Empty after strip
            portfolio_type=PortfolioType.TAXABLE
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Portfolio name cannot be empty"):
            portfolio_service.create_portfolio(tenant_id, portfolio_data)

    def test_create_portfolio_with_long_name_raises_error(self, portfolio_service):
        """Test that creating portfolio with name too long raises ValueError"""
        # Arrange
        tenant_id = 1
        portfolio_data = PortfolioCreate(
            name="x" * 101,  # 101 characters
            portfolio_type=PortfolioType.TAXABLE
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Portfolio name cannot exceed 100 characters"):
            portfolio_service.create_portfolio(tenant_id, portfolio_data)

    def test_get_portfolios_returns_tenant_portfolios(self, portfolio_service, sample_portfolio_data):
        """Test that get_portfolios returns only portfolios for the specified tenant"""
        # Arrange
        tenant_id = 1
        portfolio1 = portfolio_service.create_portfolio(tenant_id, sample_portfolio_data)

        # Create another portfolio with different data
        portfolio_data2 = PortfolioCreate(
            name="Second Portfolio",
            portfolio_type=PortfolioType.RETIREMENT
        )
        portfolio2 = portfolio_service.create_portfolio(tenant_id, portfolio_data2)

        # Act
        portfolios = portfolio_service.get_portfolios(tenant_id)

        # Assert
        assert len(portfolios) == 2
        portfolio_ids = [p.id for p in portfolios]
        assert portfolio1.id in portfolio_ids
        assert portfolio2.id in portfolio_ids

    def test_get_portfolio_success(self, portfolio_service, sample_portfolio_data):
        """Test successful retrieval of a specific portfolio"""
        # Arrange
        tenant_id = 1
        created_portfolio = portfolio_service.create_portfolio(tenant_id, sample_portfolio_data)

        # Act
        retrieved_portfolio = portfolio_service.get_portfolio(created_portfolio.id, tenant_id)

        # Assert
        assert retrieved_portfolio is not None
        assert retrieved_portfolio.id == created_portfolio.id
        assert retrieved_portfolio.name == created_portfolio.name
        assert retrieved_portfolio.portfolio_type == created_portfolio.portfolio_type

    def test_get_portfolio_nonexistent_returns_none(self, portfolio_service):
        """Test that getting non-existent portfolio returns None"""
        # Arrange
        tenant_id = 1
        nonexistent_id = 999

        # Act
        portfolio = portfolio_service.get_portfolio(nonexistent_id, tenant_id)

        # Assert
        assert portfolio is None

    def test_update_portfolio_name_success(self, portfolio_service, sample_portfolio_data):
        """Test successful portfolio name update"""
        # Arrange
        tenant_id = 1
        portfolio = portfolio_service.create_portfolio(tenant_id, sample_portfolio_data)

        update_data = PortfolioUpdate(name="Updated Portfolio Name")

        # Act
        updated_portfolio = portfolio_service.update_portfolio(portfolio.id, tenant_id, update_data)

        # Assert
        assert updated_portfolio is not None
        assert updated_portfolio.name == "Updated Portfolio Name"
        assert updated_portfolio.portfolio_type == PortfolioType.TAXABLE  # Unchanged

    def test_update_portfolio_type_success(self, portfolio_service, sample_portfolio_data):
        """Test successful portfolio type update"""
        # Arrange
        tenant_id = 1
        portfolio = portfolio_service.create_portfolio(tenant_id, sample_portfolio_data)

        update_data = PortfolioUpdate(portfolio_type=PortfolioType.RETIREMENT)

        # Act
        updated_portfolio = portfolio_service.update_portfolio(portfolio.id, tenant_id, update_data)

        # Assert
        assert updated_portfolio is not None
        assert updated_portfolio.portfolio_type == PortfolioType.RETIREMENT
        assert updated_portfolio.name == "Test Portfolio"  # Unchanged

    def test_update_portfolio_empty_name_raises_error(self, portfolio_service, sample_portfolio_data):
        """Test that updating portfolio with empty name raises ValueError"""
        # Arrange
        tenant_id = 1
        portfolio = portfolio_service.create_portfolio(tenant_id, sample_portfolio_data)

        update_data = PortfolioUpdate(name="   ")  # Empty after strip

        # Act & Assert
        with pytest.raises(ValueError, match="Portfolio name cannot be empty"):
            portfolio_service.update_portfolio(portfolio.id, tenant_id, update_data)

    def test_delete_portfolio_without_holdings_success(self, portfolio_service, sample_portfolio_data):
        """Test successful deletion of portfolio without holdings"""
        # Arrange
        tenant_id = 1
        portfolio = portfolio_service.create_portfolio(tenant_id, sample_portfolio_data)

        # Act
        result = portfolio_service.delete_portfolio(portfolio.id, tenant_id)

        # Assert
        assert result == True

        # Verify portfolio is archived
        deleted_portfolio = portfolio_service.get_portfolio(portfolio.id, tenant_id)
        assert deleted_portfolio is None  # Should not be returned as it's archived

    def test_delete_portfolio_with_holdings_raises_error(self, portfolio_service, investment_db_session, sample_portfolio_data):
        """Test that deleting portfolio with holdings raises ValueError"""
        # Arrange
        tenant_id = 1
        portfolio = portfolio_service.create_portfolio(tenant_id, sample_portfolio_data)

        # Create a holding for this portfolio
        holding = InvestmentHolding(
            portfolio_id=portfolio.id,
            security_symbol="AAPL",
            security_name="Apple Inc.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('10'),
            cost_basis=Decimal('1000'),
            purchase_date=datetime.now().date(),
            is_closed=False
        )
        investment_db_session.add(holding)
        investment_db_session.commit()

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot delete portfolio with 1 active holdings"):
            portfolio_service.delete_portfolio(portfolio.id, tenant_id)

    def test_delete_nonexistent_portfolio_returns_false(self, portfolio_service):
        """Test that deleting non-existent portfolio returns False"""
        # Arrange
        tenant_id = 1
        nonexistent_id = 999

        # Act
        result = portfolio_service.delete_portfolio(nonexistent_id, tenant_id)

        # Assert
        assert result == False

    def test_validate_tenant_access_success(self, portfolio_service, sample_portfolio_data):
        """Test successful tenant access validation"""
        # Arrange
        tenant_id = 1
        portfolio = portfolio_service.create_portfolio(tenant_id, sample_portfolio_data)

        # Act
        has_access = portfolio_service.validate_tenant_access(portfolio.id, tenant_id)

        # Assert
        assert has_access == True

    def test_validate_tenant_access_nonexistent_portfolio(self, portfolio_service):
        """Test tenant access validation for non-existent portfolio"""
        # Arrange
        tenant_id = 1
        nonexistent_id = 999

        # Act
        has_access = portfolio_service.validate_tenant_access(nonexistent_id, tenant_id)

        # Assert
        assert has_access == False

    def test_get_portfolio_with_summary(self, portfolio_service, investment_db_session, sample_portfolio_data):
        """Test getting portfolio with summary information"""
        # Arrange
        tenant_id = 1
        portfolio = portfolio_service.create_portfolio(tenant_id, sample_portfolio_data)

        # Create a holding for this portfolio
        holding = InvestmentHolding(
            portfolio_id=portfolio.id,
            security_symbol="AAPL",
            security_name="Apple Inc.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('10'),
            cost_basis=Decimal('1000'),
            purchase_date=datetime.now().date(),
            current_price=Decimal('150'),
            is_closed=False
        )
        investment_db_session.add(holding)
        investment_db_session.commit()

        # Act
        result = portfolio_service.get_portfolio_with_summary(portfolio.id, tenant_id)

        # Assert
        assert result is not None
        portfolio_result, summary = result

        assert portfolio_result.id == portfolio.id
        assert summary['holdings_count'] == 1
        assert summary['total_value'] == Decimal('1500')  # 10 * 150
        assert summary['total_cost_basis'] == Decimal('1000')
        assert summary['unrealized_gain_loss'] == Decimal('500')  # 1500 - 1000

    def test_get_portfolios_by_type(self, portfolio_service):
        """Test getting portfolios filtered by type"""
        # Arrange
        tenant_id = 1

        # Create portfolios of different types
        taxable_data = PortfolioCreate(name="Taxable Portfolio", portfolio_type=PortfolioType.TAXABLE)
        retirement_data = PortfolioCreate(name="Retirement Portfolio", portfolio_type=PortfolioType.RETIREMENT)
        business_data = PortfolioCreate(name="Business Portfolio", portfolio_type=PortfolioType.BUSINESS)

        taxable_portfolio = portfolio_service.create_portfolio(tenant_id, taxable_data)
        retirement_portfolio = portfolio_service.create_portfolio(tenant_id, retirement_data)
        business_portfolio = portfolio_service.create_portfolio(tenant_id, business_data)

        # Act
        taxable_portfolios = portfolio_service.get_portfolios_by_type(tenant_id, PortfolioType.TAXABLE)
        retirement_portfolios = portfolio_service.get_portfolios_by_type(tenant_id, PortfolioType.RETIREMENT)

        # Assert
        assert len(taxable_portfolios) == 1
        assert taxable_portfolios[0].id == taxable_portfolio.id

        assert len(retirement_portfolios) == 1
        assert retirement_portfolios[0].id == retirement_portfolio.id

    def test_count_portfolios_by_type(self, portfolio_service):
        """Test counting portfolios by type"""
        # Arrange
        tenant_id = 1

        # Create multiple portfolios of same type
        for i in range(3):
            portfolio_data = PortfolioCreate(
                name=f"Taxable Portfolio {i}",
                portfolio_type=PortfolioType.TAXABLE
            )
            portfolio_service.create_portfolio(tenant_id, portfolio_data)

        # Create one retirement portfolio
        retirement_data = PortfolioCreate(
            name="Retirement Portfolio",
            portfolio_type=PortfolioType.RETIREMENT
        )
        portfolio_service.create_portfolio(tenant_id, retirement_data)

        # Act
        taxable_count = portfolio_service.count_portfolios_by_type(tenant_id, PortfolioType.TAXABLE)
        retirement_count = portfolio_service.count_portfolios_by_type(tenant_id, PortfolioType.RETIREMENT)
        business_count = portfolio_service.count_portfolios_by_type(tenant_id, PortfolioType.BUSINESS)

        # Assert
        assert taxable_count == 3
        assert retirement_count == 1
        assert business_count == 0

    def test_portfolio_exists(self, portfolio_service, sample_portfolio_data):
        """Test portfolio existence check"""
        # Arrange
        tenant_id = 1
        portfolio = portfolio_service.create_portfolio(tenant_id, sample_portfolio_data)

        # Act & Assert
        assert portfolio_service.portfolio_exists(portfolio.id, tenant_id) == True
        assert portfolio_service.portfolio_exists(999, tenant_id) == False

    def test_service_close(self, investment_db_session):
        """Test that service properly closes resources"""
        # Arrange
        service = PortfolioService(investment_db_session)

        # Act
        service.close()

        # Assert - no exception should be raised
        assert True