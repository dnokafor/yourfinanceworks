"""
Test Business Portfolio Support

This module tests the business portfolio functionality added in task 14.1.
It verifies that business portfolios can be created, filtered, and analyzed
separately from personal portfolios.
"""

import pytest
from decimal import Decimal
from datetime import date

from plugins.investments.models import PortfolioType, SecurityType, AssetClass
from plugins.investments.schemas import PortfolioCreate, HoldingCreate
from plugins.investments.services.portfolio_service import PortfolioService
from plugins.investments.services.holdings_service import HoldingsService
from plugins.investments.services.analytics_service import AnalyticsService


class TestBusinessPortfolioSupport:
    """Test business portfolio functionality"""

    def test_create_business_portfolio(self, db_session):
        """Test creating a business portfolio"""
        # Arrange
        tenant_id = 1
        portfolio_data = PortfolioCreate(
            name="Business Investment Portfolio",
            portfolio_type=PortfolioType.BUSINESS
        )

        # Act
        service = PortfolioService(db_session)
        portfolio = service.create_portfolio(tenant_id, portfolio_data)

        # Assert
        assert portfolio is not None
        assert portfolio.name == "Business Investment Portfolio"
        assert portfolio.portfolio_type == PortfolioType.BUSINESS
        assert not portfolio.is_archived

    def test_get_portfolios_by_business_type(self, db_session):
        """Test filtering portfolios by business type"""
        # Arrange
        tenant_id = 1
        service = PortfolioService(db_session)

        # Create different portfolio types
        business_portfolio = service.create_portfolio(
            tenant_id,
            PortfolioCreate(name="Business Portfolio", portfolio_type=PortfolioType.BUSINESS)
        )
        taxable_portfolio = service.create_portfolio(
            tenant_id,
            PortfolioCreate(name="Personal Portfolio", portfolio_type=PortfolioType.TAXABLE)
        )

        # Act
        business_portfolios = service.get_portfolios_by_type(
            tenant_id, PortfolioType.BUSINESS
        )
        taxable_portfolios = service.get_portfolios_by_type(
            tenant_id, PortfolioType.TAXABLE
        )

        # Assert
        assert len(business_portfolios) == 1
        assert business_portfolios[0].portfolio_type == PortfolioType.BUSINESS
        assert business_portfolios[0].name == "Business Portfolio"

        assert len(taxable_portfolios) == 1
        assert taxable_portfolios[0].portfolio_type == PortfolioType.TAXABLE
        assert taxable_portfolios[0].name == "Personal Portfolio"

    def test_count_portfolios_by_business_type(self, db_session):
        """Test counting portfolios by business type"""
        # Arrange
        tenant_id = 1
        service = PortfolioService(db_session)

        # Create business portfolios
        service.create_portfolio(
            tenant_id,
            PortfolioCreate(name="Business Portfolio 1", portfolio_type=PortfolioType.BUSINESS)
        )
        service.create_portfolio(
            tenant_id,
            PortfolioCreate(name="Business Portfolio 2", portfolio_type=PortfolioType.BUSINESS)
        )

        # Act
        business_count = service.count_portfolios_by_type(tenant_id, PortfolioType.BUSINESS)

        # Assert
        assert business_count == 2

    def test_business_portfolio_supports_all_security_types(self, db_session):
        """Test that business portfolios support all security types"""
        # Arrange
        tenant_id = 1
        portfolio_service = PortfolioService(db_session)
        holdings_service = HoldingsService(db_session)

        # Create business portfolio
        portfolio = portfolio_service.create_portfolio(
            tenant_id,
            PortfolioCreate(name="Business Portfolio", portfolio_type=PortfolioType.BUSINESS)
        )

        # Test all security types
        security_types = [
            SecurityType.STOCK,
            SecurityType.BOND,
            SecurityType.ETF,
            SecurityType.MUTUAL_FUND,
            SecurityType.CASH
        ]

        # Act & Assert
        for i, security_type in enumerate(security_types):
            holding_data = HoldingCreate(
                security_symbol=f"TEST{i}",
                security_name=f"Test {security_type.value}",
                security_type=security_type,
                asset_class=AssetClass.STOCKS if security_type == SecurityType.STOCK else AssetClass.BONDS,
                quantity=Decimal("100"),
                cost_basis=Decimal("1000"),
                purchase_date=date.today()
            )

            holding = holdings_service.create_holding(portfolio.id, holding_data)

            assert holding is not None
            assert holding.security_type == security_type
            assert holding.portfolio_id == portfolio.id

    def test_aggregated_analytics_by_business_type(self, db_session):
        """Test aggregated analytics filtered by business type"""
        # Arrange
        tenant_id = 1
        portfolio_service = PortfolioService(db_session)
        holdings_service = HoldingsService(db_session)
        analytics_service = AnalyticsService(db_session)

        # Create business and personal portfolios
        business_portfolio = portfolio_service.create_portfolio(
            tenant_id,
            PortfolioCreate(name="Business Portfolio", portfolio_type=PortfolioType.BUSINESS)
        )
        personal_portfolio = portfolio_service.create_portfolio(
            tenant_id,
            PortfolioCreate(name="Personal Portfolio", portfolio_type=PortfolioType.TAXABLE)
        )

        # Add holdings to business portfolio
        business_holding = holdings_service.create_holding(
            business_portfolio.id,
            HoldingCreate(
                security_symbol="BUSSTOCK",
                security_name="Business Stock",
                security_type=SecurityType.STOCK,
                asset_class=AssetClass.STOCKS,
                quantity=Decimal("100"),
                cost_basis=Decimal("5000"),
                purchase_date=date.today()
            )
        )

        # Add holdings to personal portfolio
        personal_holding = holdings_service.create_holding(
            personal_portfolio.id,
            HoldingCreate(
                security_symbol="PERSTOCK",
                security_name="Personal Stock",
                security_type=SecurityType.STOCK,
                asset_class=AssetClass.STOCKS,
                quantity=Decimal("50"),
                cost_basis=Decimal("2500"),
                purchase_date=date.today()
            )
        )

        # Act
        all_analytics = analytics_service.get_aggregated_analytics_by_type(tenant_id)
        business_analytics = analytics_service.get_aggregated_analytics_by_type(
            tenant_id, PortfolioType.BUSINESS
        )

        # Assert
        assert all_analytics["portfolio_count"] == 2
        assert all_analytics["total_cost"] == 7500.0  # 5000 + 2500

        assert business_analytics["portfolio_count"] == 1
        assert business_analytics["total_cost"] == 5000.0  # Only business portfolio
        assert business_analytics["portfolio_type_filter"] == "business"

    def test_business_data_separation(self, db_session):
        """Test that business investment data is properly separated"""
        # Arrange
        tenant_id = 1
        portfolio_service = PortfolioService(db_session)

        # Create portfolios of different types
        business_portfolio = portfolio_service.create_portfolio(
            tenant_id,
            PortfolioCreate(name="Business Portfolio", portfolio_type=PortfolioType.BUSINESS)
        )
        retirement_portfolio = portfolio_service.create_portfolio(
            tenant_id,
            PortfolioCreate(name="Retirement Portfolio", portfolio_type=PortfolioType.RETIREMENT)
        )
        taxable_portfolio = portfolio_service.create_portfolio(
            tenant_id,
            PortfolioCreate(name="Taxable Portfolio", portfolio_type=PortfolioType.TAXABLE)
        )

        # Act
        business_portfolios = portfolio_service.get_portfolios_by_type(
            tenant_id, PortfolioType.BUSINESS
        )
        retirement_portfolios = portfolio_service.get_portfolios_by_type(
            tenant_id, PortfolioType.RETIREMENT
        )
        taxable_portfolios = portfolio_service.get_portfolios_by_type(
            tenant_id, PortfolioType.TAXABLE
        )

        # Assert - Each type should only contain its own portfolios
        assert len(business_portfolios) == 1
        assert all(p.portfolio_type == PortfolioType.BUSINESS for p in business_portfolios)

        assert len(retirement_portfolios) == 1
        assert all(p.portfolio_type == PortfolioType.RETIREMENT for p in retirement_portfolios)

        assert len(taxable_portfolios) == 1
        assert all(p.portfolio_type == PortfolioType.TAXABLE for p in taxable_portfolios)

        # Verify no cross-contamination
        business_ids = {p.id for p in business_portfolios}
        retirement_ids = {p.id for p in retirement_portfolios}
        taxable_ids = {p.id for p in taxable_portfolios}

        assert business_ids.isdisjoint(retirement_ids)
        assert business_ids.isdisjoint(taxable_ids)
        assert retirement_ids.isdisjoint(taxable_ids)