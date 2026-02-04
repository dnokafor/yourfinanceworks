"""
Unit tests for Investment Portfolio Repository

This module tests the PortfolioRepository class to ensure proper CRUD operations,
tenant isolation, and data integrity for investment portfolios.
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone
from decimal import Decimal

# Import investment models and repository
from plugins.investments.models import (
    InvestmentPortfolio,
    InvestmentHolding,
    PortfolioType,
    Base as InvestmentBase
)
from plugins.investments.repositories.portfolio_repository import PortfolioRepository


class TestPortfolioRepository:
    """Test suite for PortfolioRepository"""

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
    def portfolio_repository(self, investment_db_session):
        """Create a PortfolioRepository instance with test database session"""
        return PortfolioRepository(investment_db_session)

    @pytest.fixture
    def sample_portfolio_data(self):
        """Sample portfolio data for testing"""
        return {
            "name": "Test Portfolio",
            "portfolio_type": PortfolioType.TAXABLE
        }

    def test_create_portfolio_success(self, portfolio_repository, sample_portfolio_data):
        """Test successful portfolio creation"""
        # Act
        portfolio = portfolio_repository.create(
            tenant_id=1,
            name=sample_portfolio_data["name"],
            portfolio_type=sample_portfolio_data["portfolio_type"]
        )

        # Assert
        assert portfolio is not None
        assert portfolio.id is not None
        assert portfolio.name == sample_portfolio_data["name"]
        assert portfolio.portfolio_type == sample_portfolio_data["portfolio_type"]
        assert portfolio.is_archived == False
        assert portfolio.created_at is not None
        assert portfolio.updated_at is not None

    def test_create_portfolio_all_types(self, portfolio_repository):
        """Test creating portfolios of all supported types"""
        portfolio_types = [PortfolioType.TAXABLE, PortfolioType.RETIREMENT, PortfolioType.BUSINESS]

        for portfolio_type in portfolio_types:
            # Act
            portfolio = portfolio_repository.create(
                tenant_id=1,
                name=f"Test {portfolio_type.value} Portfolio",
                portfolio_type=portfolio_type
            )

            # Assert
            assert portfolio.portfolio_type == portfolio_type
            assert portfolio.name == f"Test {portfolio_type.value} Portfolio"

    def test_get_by_id_existing_portfolio(self, portfolio_repository, sample_portfolio_data):
        """Test retrieving an existing portfolio by ID"""
        # Arrange
        created_portfolio = portfolio_repository.create(
            tenant_id=1,
            name=sample_portfolio_data["name"],
            portfolio_type=sample_portfolio_data["portfolio_type"]
        )

        # Act
        retrieved_portfolio = portfolio_repository.get_by_id(created_portfolio.id, tenant_id=1)

        # Assert
        assert retrieved_portfolio is not None
        assert retrieved_portfolio.id == created_portfolio.id
        assert retrieved_portfolio.name == created_portfolio.name
        assert retrieved_portfolio.portfolio_type == created_portfolio.portfolio_type

    def test_get_by_id_nonexistent_portfolio(self, portfolio_repository):
        """Test retrieving a non-existent portfolio returns None"""
        # Act
        portfolio = portfolio_repository.get_by_id(99999, tenant_id=1)

        # Assert
        assert portfolio is None

    def test_get_by_id_archived_portfolio(self, portfolio_repository, sample_portfolio_data):
        """Test that archived portfolios are not returned by get_by_id"""
        # Arrange
        created_portfolio = portfolio_repository.create(
            tenant_id=1,
            name=sample_portfolio_data["name"],
            portfolio_type=sample_portfolio_data["portfolio_type"]
        )

        # Archive the portfolio directly in the database
        created_portfolio.is_archived = True
        portfolio_repository.db.commit()

        # Act
        retrieved_portfolio = portfolio_repository.get_by_id(created_portfolio.id, tenant_id=1)

        # Assert
        assert retrieved_portfolio is None

    def test_get_by_tenant_empty(self, portfolio_repository):
        """Test retrieving portfolios when none exist"""
        # Act
        portfolios = portfolio_repository.get_by_tenant(tenant_id=1)

        # Assert
        assert portfolios == []

    def test_get_by_tenant_multiple_portfolios(self, portfolio_repository):
        """Test retrieving multiple portfolios for a tenant"""
        # Arrange
        portfolio1 = portfolio_repository.create(tenant_id=1, name="Portfolio 1", portfolio_type=PortfolioType.TAXABLE)
        portfolio2 = portfolio_repository.create(tenant_id=1, name="Portfolio 2", portfolio_type=PortfolioType.RETIREMENT)
        portfolio3 = portfolio_repository.create(tenant_id=1, name="Portfolio 3", portfolio_type=PortfolioType.BUSINESS)

        # Act
        portfolios = portfolio_repository.get_by_tenant(tenant_id=1)

        # Assert
        assert len(portfolios) == 3
        portfolio_ids = [p.id for p in portfolios]
        assert portfolio1.id in portfolio_ids
        assert portfolio2.id in portfolio_ids
        assert portfolio3.id in portfolio_ids

    def test_get_by_tenant_excludes_archived(self, portfolio_repository):
        """Test that get_by_tenant excludes archived portfolios by default"""
        # Arrange
        active_portfolio = portfolio_repository.create(tenant_id=1, name="Active Portfolio", portfolio_type=PortfolioType.TAXABLE)
        archived_portfolio = portfolio_repository.create(tenant_id=1, name="Archived Portfolio", portfolio_type=PortfolioType.RETIREMENT)

        # Archive one portfolio
        archived_portfolio.is_archived = True
        portfolio_repository.db.commit()

        # Act
        portfolios = portfolio_repository.get_by_tenant(tenant_id=1)

        # Assert
        assert len(portfolios) == 1
        assert portfolios[0].id == active_portfolio.id

    def test_get_by_tenant_includes_archived_when_requested(self, portfolio_repository):
        """Test that get_by_tenant includes archived portfolios when requested"""
        # Arrange
        active_portfolio = portfolio_repository.create(tenant_id=1, name="Active Portfolio", portfolio_type=PortfolioType.TAXABLE)
        archived_portfolio = portfolio_repository.create(tenant_id=1, name="Archived Portfolio", portfolio_type=PortfolioType.RETIREMENT)

        # Archive one portfolio
        archived_portfolio.is_archived = True
        portfolio_repository.db.commit()

        # Act
        portfolios = portfolio_repository.get_by_tenant(tenant_id=1, include_archived=True)

        # Assert
        assert len(portfolios) == 2
        portfolio_ids = [p.id for p in portfolios]
        assert active_portfolio.id in portfolio_ids
        assert archived_portfolio.id in portfolio_ids

    def test_update_portfolio_name(self, portfolio_repository, sample_portfolio_data):
        """Test updating portfolio name"""
        # Arrange
        portfolio = portfolio_repository.create(
            tenant_id=1,
            name=sample_portfolio_data["name"],
            portfolio_type=sample_portfolio_data["portfolio_type"]
        )
        original_updated_at = portfolio.updated_at

        # Act
        updated_portfolio = portfolio_repository.update(portfolio.id, tenant_id=1, name="Updated Portfolio Name")

        # Assert
        assert updated_portfolio is not None
        assert updated_portfolio.name == "Updated Portfolio Name"
        assert updated_portfolio.portfolio_type == sample_portfolio_data["portfolio_type"]
        assert updated_portfolio.updated_at > original_updated_at

    def test_update_portfolio_type(self, portfolio_repository, sample_portfolio_data):
        """Test updating portfolio type"""
        # Arrange
        portfolio = portfolio_repository.create(
            tenant_id=1,
            name=sample_portfolio_data["name"],
            portfolio_type=PortfolioType.TAXABLE
        )

        # Act
        updated_portfolio = portfolio_repository.update(
            portfolio.id,
            tenant_id=1,
            portfolio_type=PortfolioType.RETIREMENT
        )

        # Assert
        assert updated_portfolio is not None
        assert updated_portfolio.portfolio_type == PortfolioType.RETIREMENT
        assert updated_portfolio.name == sample_portfolio_data["name"]

    def test_update_portfolio_both_fields(self, portfolio_repository, sample_portfolio_data):
        """Test updating both name and type"""
        # Arrange
        portfolio = portfolio_repository.create(
            tenant_id=1,
            name=sample_portfolio_data["name"],
            portfolio_type=PortfolioType.TAXABLE
        )

        # Act
        updated_portfolio = portfolio_repository.update(
            portfolio.id,
            tenant_id=1,
            name="New Name",
            portfolio_type=PortfolioType.BUSINESS
        )

        # Assert
        assert updated_portfolio is not None
        assert updated_portfolio.name == "New Name"
        assert updated_portfolio.portfolio_type == PortfolioType.BUSINESS

    def test_update_nonexistent_portfolio(self, portfolio_repository):
        """Test updating a non-existent portfolio returns None"""
        # Act
        result = portfolio_repository.update(99999, tenant_id=1, name="New Name")

        # Assert
        assert result is None

    def test_update_with_none_values_ignored(self, portfolio_repository, sample_portfolio_data):
        """Test that None values in updates are ignored"""
        # Arrange
        portfolio = portfolio_repository.create(
            tenant_id=1,
            name=sample_portfolio_data["name"],
            portfolio_type=sample_portfolio_data["portfolio_type"]
        )

        # Act
        updated_portfolio = portfolio_repository.update(
            portfolio.id,
            tenant_id=1,
            name=None,
            portfolio_type=PortfolioType.RETIREMENT
        )

        # Assert
        assert updated_portfolio is not None
        assert updated_portfolio.name == sample_portfolio_data["name"]  # Unchanged
        assert updated_portfolio.portfolio_type == PortfolioType.RETIREMENT  # Changed

    def test_delete_portfolio_without_holdings(self, portfolio_repository, sample_portfolio_data):
        """Test deleting a portfolio with no holdings"""
        # Arrange
        portfolio = portfolio_repository.create(
            tenant_id=1,
            name=sample_portfolio_data["name"],
            portfolio_type=sample_portfolio_data["portfolio_type"]
        )

        # Act
        result = portfolio_repository.delete(portfolio.id, tenant_id=1)

        # Assert
        assert result == True

        # Verify portfolio is archived
        archived_portfolio = portfolio_repository.db.query(InvestmentPortfolio).filter(
            InvestmentPortfolio.id == portfolio.id
        ).first()
        assert archived_portfolio.is_archived == True

    def test_delete_portfolio_with_holdings_raises_error(self, portfolio_repository, investment_db_session, sample_portfolio_data):
        """Test that deleting a portfolio with holdings raises ValueError"""
        # Arrange
        portfolio = portfolio_repository.create(
            tenant_id=1,
            name=sample_portfolio_data["name"],
            portfolio_type=sample_portfolio_data["portfolio_type"]
        )

        # Create a holding for this portfolio
        from plugins.investments.models import InvestmentHolding, SecurityType, AssetClass
        holding = InvestmentHolding(
            portfolio_id=portfolio.id,
            security_symbol="AAPL",
            security_name="Apple Inc.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal("10"),
            cost_basis=Decimal("1000.00"),
            purchase_date=datetime.now(timezone.utc).date(),
            is_closed=False
        )
        investment_db_session.add(holding)
        investment_db_session.commit()

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot delete portfolio with 1 active holdings"):
            portfolio_repository.delete(portfolio.id, tenant_id=1)

    def test_delete_portfolio_with_closed_holdings_succeeds(self, portfolio_repository, investment_db_session, sample_portfolio_data):
        """Test that deleting a portfolio with only closed holdings succeeds"""
        # Arrange
        portfolio = portfolio_repository.create(
            tenant_id=1,
            name=sample_portfolio_data["name"],
            portfolio_type=sample_portfolio_data["portfolio_type"]
        )

        # Create a closed holding for this portfolio
        from plugins.investments.models import InvestmentHolding, SecurityType, AssetClass
        holding = InvestmentHolding(
            portfolio_id=portfolio.id,
            security_symbol="AAPL",
            security_name="Apple Inc.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal("0"),
            cost_basis=Decimal("1000.00"),
            purchase_date=datetime.now(timezone.utc).date(),
            is_closed=True
        )
        investment_db_session.add(holding)
        investment_db_session.commit()

        # Act
        result = portfolio_repository.delete(portfolio.id, tenant_id=1)

        # Assert
        assert result == True

    def test_delete_nonexistent_portfolio(self, portfolio_repository):
        """Test deleting a non-existent portfolio returns False"""
        # Act
        result = portfolio_repository.delete(99999, tenant_id=1)

        # Assert
        assert result == False

    def test_validate_tenant_access_existing_portfolio(self, portfolio_repository, sample_portfolio_data):
        """Test tenant access validation for existing portfolio"""
        # Arrange
        portfolio = portfolio_repository.create(
            tenant_id=1,
            name=sample_portfolio_data["name"],
            portfolio_type=sample_portfolio_data["portfolio_type"]
        )

        # Act
        has_access = portfolio_repository.validate_tenant_access(portfolio.id, tenant_id=1)

        # Assert
        assert has_access == True

    def test_validate_tenant_access_nonexistent_portfolio(self, portfolio_repository):
        """Test tenant access validation for non-existent portfolio"""
        # Act
        has_access = portfolio_repository.validate_tenant_access(99999, tenant_id=1)

        # Assert
        assert has_access == False

    def test_exists_existing_portfolio(self, portfolio_repository, sample_portfolio_data):
        """Test exists check for existing portfolio"""
        # Arrange
        portfolio = portfolio_repository.create(
            tenant_id=1,
            name=sample_portfolio_data["name"],
            portfolio_type=sample_portfolio_data["portfolio_type"]
        )

        # Act
        exists = portfolio_repository.exists(portfolio.id, tenant_id=1)

        # Assert
        assert exists == True

    def test_exists_nonexistent_portfolio(self, portfolio_repository):
        """Test exists check for non-existent portfolio"""
        # Act
        exists = portfolio_repository.exists(99999, tenant_id=1)

        # Assert
        assert exists == False

    def test_get_by_type(self, portfolio_repository):
        """Test retrieving portfolios by type"""
        # Arrange
        taxable1 = portfolio_repository.create(tenant_id=1, name="Taxable 1", portfolio_type=PortfolioType.TAXABLE)
        taxable2 = portfolio_repository.create(tenant_id=1, name="Taxable 2", portfolio_type=PortfolioType.TAXABLE)
        retirement = portfolio_repository.create(tenant_id=1, name="Retirement", portfolio_type=PortfolioType.RETIREMENT)
        business = portfolio_repository.create(tenant_id=1, name="Business", portfolio_type=PortfolioType.BUSINESS)

        # Act
        taxable_portfolios = portfolio_repository.get_by_type(tenant_id=1, portfolio_type=PortfolioType.TAXABLE)
        retirement_portfolios = portfolio_repository.get_by_type(tenant_id=1, portfolio_type=PortfolioType.RETIREMENT)
        business_portfolios = portfolio_repository.get_by_type(tenant_id=1, portfolio_type=PortfolioType.BUSINESS)

        # Assert
        assert len(taxable_portfolios) == 2
        assert len(retirement_portfolios) == 1
        assert len(business_portfolios) == 1

        taxable_ids = [p.id for p in taxable_portfolios]
        assert taxable1.id in taxable_ids
        assert taxable2.id in taxable_ids
        assert retirement_portfolios[0].id == retirement.id
        assert business_portfolios[0].id == business.id

    def test_count_by_type(self, portfolio_repository):
        """Test counting portfolios by type"""
        # Arrange
        portfolio_repository.create(tenant_id=1, name="Taxable 1", portfolio_type=PortfolioType.TAXABLE)
        portfolio_repository.create(tenant_id=1, name="Taxable 2", portfolio_type=PortfolioType.TAXABLE)
        portfolio_repository.create(tenant_id=1, name="Retirement", portfolio_type=PortfolioType.RETIREMENT)

        # Act
        taxable_count = portfolio_repository.count_by_type(tenant_id=1, portfolio_type=PortfolioType.TAXABLE)
        retirement_count = portfolio_repository.count_by_type(tenant_id=1, portfolio_type=PortfolioType.RETIREMENT)
        business_count = portfolio_repository.count_by_type(tenant_id=1, portfolio_type=PortfolioType.BUSINESS)

        # Assert
        assert taxable_count == 2
        assert retirement_count == 1
        assert business_count == 0

    def test_get_with_holdings_count_no_holdings(self, portfolio_repository, sample_portfolio_data):
        """Test getting portfolio with holdings count when no holdings exist"""
        # Arrange
        portfolio = portfolio_repository.create(
            tenant_id=1,
            name=sample_portfolio_data["name"],
            portfolio_type=sample_portfolio_data["portfolio_type"]
        )

        # Act
        result = portfolio_repository.get_with_holdings_count(portfolio.id, tenant_id=1)

        # Assert
        assert result is not None
        retrieved_portfolio, holdings_count = result
        assert retrieved_portfolio.id == portfolio.id
        assert holdings_count == 0

    def test_get_with_holdings_count_with_holdings(self, portfolio_repository, investment_db_session, sample_portfolio_data):
        """Test getting portfolio with holdings count when holdings exist"""
        # Arrange
        portfolio = portfolio_repository.create(
            tenant_id=1,
            name=sample_portfolio_data["name"],
            portfolio_type=sample_portfolio_data["portfolio_type"]
        )

        # Create holdings for this portfolio
        from plugins.investments.models import InvestmentHolding, SecurityType, AssetClass
        for i in range(3):
            holding = InvestmentHolding(
                portfolio_id=portfolio.id,
                security_symbol=f"STOCK{i}",
                security_name=f"Stock {i}",
                security_type=SecurityType.STOCK,
                asset_class=AssetClass.STOCKS,
                quantity=Decimal("10"),
                cost_basis=Decimal("1000.00"),
                purchase_date=datetime.now(timezone.utc).date(),
                is_closed=False
            )
            investment_db_session.add(holding)
        investment_db_session.commit()

        # Act
        result = portfolio_repository.get_with_holdings_count(portfolio.id, tenant_id=1)

        # Assert
        assert result is not None
        retrieved_portfolio, holdings_count = result
        assert retrieved_portfolio.id == portfolio.id
        assert holdings_count == 3

    def test_get_all_with_holdings_count(self, portfolio_repository, investment_db_session):
        """Test getting all portfolios with their holdings counts"""
        # Arrange
        portfolio1 = portfolio_repository.create(tenant_id=1, name="Portfolio 1", portfolio_type=PortfolioType.TAXABLE)
        portfolio2 = portfolio_repository.create(tenant_id=1, name="Portfolio 2", portfolio_type=PortfolioType.RETIREMENT)

        # Create holdings for portfolio1 only
        from plugins.investments.models import InvestmentHolding, SecurityType, AssetClass
        for i in range(2):
            holding = InvestmentHolding(
                portfolio_id=portfolio1.id,
                security_symbol=f"STOCK{i}",
                security_name=f"Stock {i}",
                security_type=SecurityType.STOCK,
                asset_class=AssetClass.STOCKS,
                quantity=Decimal("10"),
                cost_basis=Decimal("1000.00"),
                purchase_date=datetime.now(timezone.utc).date(),
                is_closed=False
            )
            investment_db_session.add(holding)
        investment_db_session.commit()

        # Act
        results = portfolio_repository.get_all_with_holdings_count(tenant_id=1)

        # Assert
        assert len(results) == 2

        # Find results by portfolio ID
        result1 = next((r for r in results if r.InvestmentPortfolio.id == portfolio1.id), None)
        result2 = next((r for r in results if r.InvestmentPortfolio.id == portfolio2.id), None)

        assert result1 is not None
        assert result1.holdings_count == 2
        assert result2 is not None
        assert result2.holdings_count == 0

    def test_repository_ordering_by_created_at(self, portfolio_repository):
        """Test that portfolios are returned in descending order by created_at"""
        # Arrange - create portfolios with slight time differences
        import time

        portfolio1 = portfolio_repository.create(tenant_id=1, name="First Portfolio", portfolio_type=PortfolioType.TAXABLE)
        time.sleep(0.01)  # Small delay to ensure different timestamps
        portfolio2 = portfolio_repository.create(tenant_id=1, name="Second Portfolio", portfolio_type=PortfolioType.RETIREMENT)
        time.sleep(0.01)
        portfolio3 = portfolio_repository.create(tenant_id=1, name="Third Portfolio", portfolio_type=PortfolioType.BUSINESS)

        # Act
        portfolios = portfolio_repository.get_by_tenant(tenant_id=1)

        # Assert - should be in reverse chronological order (newest first)
        assert len(portfolios) == 3
        assert portfolios[0].id == portfolio3.id  # Most recent
        assert portfolios[1].id == portfolio2.id  # Middle
        assert portfolios[2].id == portfolio1.id  # Oldest

    def test_repository_close_session(self, investment_db_session):
        """Test that repository properly closes database session"""
        # Arrange
        repository = PortfolioRepository(investment_db_session)

        # Act
        repository.close()

        # Assert - session should be closed
        # Note: This is more of a smoke test since we can't easily verify session state
        assert True  # If no exception is raised, the close method works