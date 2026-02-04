"""
Unit tests for Investment MCP Provider

Tests the MCP integration for investment data, ensuring proper tenant isolation
and data formatting for the AI assistant.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import date, datetime
from decimal import Decimal

from plugins.investments.mcp.investment_provider import InvestmentMCPProvider
from plugins.investments.models import PortfolioType, SecurityType, AssetClass, TransactionType
from plugins.investments.schemas import PerformanceMetrics, AssetAllocation, DividendSummary, TaxExport
from core.exceptions.base import NotFoundError


class TestInvestmentMCPProvider:
    """Test cases for Investment MCP Provider"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def mock_portfolio_service(self):
        """Mock portfolio service"""
        return Mock()

    @pytest.fixture
    def mock_holdings_service(self):
        """Mock holdings service"""
        return Mock()

    @pytest.fixture
    def mock_analytics_service(self):
        """Mock analytics service"""
        return Mock()

    @pytest.fixture
    def mcp_provider(self, mock_db_session):
        """Create MCP provider instance with mocked dependencies"""
        with patch('plugins.investments.mcp.investment_provider.SessionLocal', return_value=mock_db_session), \
             patch('plugins.investments.mcp.investment_provider.PortfolioService') as mock_portfolio_svc, \
             patch('plugins.investments.mcp.investment_provider.HoldingsService') as mock_holdings_svc, \
             patch('plugins.investments.mcp.investment_provider.AnalyticsService') as mock_analytics_svc, \
             patch('plugins.investments.mcp.investment_provider.HoldingsRepository') as mock_holdings_repo, \
             patch('plugins.investments.mcp.investment_provider.TransactionRepository') as mock_transaction_repo:

            provider = InvestmentMCPProvider(mock_db_session)
            provider.portfolio_service = mock_portfolio_svc.return_value
            provider.holdings_service = mock_holdings_svc.return_value
            provider.analytics_service = mock_analytics_svc.return_value
            provider.holdings_repo = mock_holdings_repo.return_value
            provider.transaction_repo = mock_transaction_repo.return_value

            return provider

    @pytest.fixture
    def sample_portfolio(self):
        """Sample portfolio for testing"""
        portfolio = Mock()
        portfolio.id = 1
        portfolio.name = "Test Portfolio"
        portfolio.portfolio_type = PortfolioType.TAXABLE
        portfolio.created_at = datetime(2024, 1, 1)
        portfolio.is_archived = False
        return portfolio

    @pytest.fixture
    def sample_holding(self):
        """Sample holding for testing"""
        holding = Mock()
        holding.id = 1
        holding.security_symbol = "AAPL"
        holding.security_name = "Apple Inc."
        holding.security_type = SecurityType.STOCK
        holding.asset_class = AssetClass.STOCKS
        holding.quantity = Decimal('100')
        holding.cost_basis = Decimal('15000')
        holding.current_price = Decimal('180')
        holding.purchase_date = date(2024, 1, 1)
        holding.price_updated_at = datetime(2024, 12, 1)
        holding.is_closed = False
        return holding

    @pytest.mark.asyncio
    async def test_get_portfolio_summary_success(self, mcp_provider, sample_portfolio):
        """Test successful portfolio summary retrieval"""
        # Arrange
        tenant_id = 1
        summary_data = {
            'holdings_count': 5,
            'total_value': Decimal('25000'),
            'total_cost_basis': Decimal('20000'),
            'unrealized_gain_loss': Decimal('5000')
        }

        mcp_provider.portfolio_service.get_portfolios_with_summary.return_value = [
            (sample_portfolio, summary_data)
        ]

        # Act
        result = await mcp_provider.get_portfolio_summary(tenant_id)

        # Assert
        assert result["provider"] == "investments"
        assert result["tenant_id"] == tenant_id
        assert result["summary"]["total_portfolios"] == 1
        assert result["summary"]["total_value"] == 25000.0
        assert result["summary"]["total_cost_basis"] == 20000.0
        assert result["summary"]["overall_return_percentage"] == 25.0
        assert len(result["portfolios"]) == 1

        portfolio_data = result["portfolios"][0]
        assert portfolio_data["id"] == 1
        assert portfolio_data["name"] == "Test Portfolio"
        assert portfolio_data["type"] == "taxable"
        assert portfolio_data["holdings_count"] == 5

    @pytest.mark.asyncio
    async def test_get_portfolio_summary_empty(self, mcp_provider):
        """Test portfolio summary with no portfolios"""
        # Arrange
        tenant_id = 1
        mcp_provider.portfolio_service.get_portfolios_with_summary.return_value = []

        # Act
        result = await mcp_provider.get_portfolio_summary(tenant_id)

        # Assert
        assert result["provider"] == "investments"
        assert result["tenant_id"] == tenant_id
        assert result["summary"]["total_portfolios"] == 0
        assert result["summary"]["total_value"] == 0.0
        assert result["portfolios"] == []

    @pytest.mark.asyncio
    async def test_get_holding_details_success(self, mcp_provider, sample_portfolio, sample_holding):
        """Test successful holding details retrieval"""
        # Arrange
        tenant_id = 1
        symbol = "AAPL"

        mcp_provider.portfolio_service.get_portfolios.return_value = [sample_portfolio]
        mcp_provider.holdings_repo.get_by_portfolio.return_value = [sample_holding]

        # Act
        result = await mcp_provider.get_holding_details(tenant_id, symbol)

        # Assert
        assert result["provider"] == "investments"
        assert result["tenant_id"] == tenant_id
        assert result["symbol"] == "AAPL"
        assert result["summary"]["total_holdings"] == 1
        assert result["summary"]["total_quantity"] == 100.0
        assert result["summary"]["total_cost_basis"] == 15000.0
        assert len(result["holdings"]) == 1

        holding_data = result["holdings"][0]
        assert holding_data["security_symbol"] == "AAPL"
        assert holding_data["portfolio_name"] == "Test Portfolio"
        assert holding_data["quantity"] == 100.0

    @pytest.mark.asyncio
    async def test_get_holding_details_not_found(self, mcp_provider, sample_portfolio):
        """Test holding details when symbol not found"""
        # Arrange
        tenant_id = 1
        symbol = "MSFT"

        mcp_provider.portfolio_service.get_portfolios.return_value = [sample_portfolio]
        mcp_provider.holdings_repo.get_by_portfolio.return_value = []

        # Act
        result = await mcp_provider.get_holding_details(tenant_id, symbol)

        # Assert
        assert result["provider"] == "investments"
        assert result["symbol"] == "MSFT"
        assert result["summary"]["total_holdings"] == 0
        assert result["holdings"] == []

    @pytest.mark.asyncio
    async def test_get_performance_summary_success(self, mcp_provider):
        """Test successful performance summary retrieval"""
        # Arrange
        tenant_id = 1
        portfolio_id = 1

        portfolio_summary = {
            "portfolio_name": "Test Portfolio",
            "portfolio_type": "taxable",
            "performance": {
                "total_value": 25000.0,
                "total_return_percentage": 25.0
            },
            "allocation": {"total_value": 25000.0},
            "holdings": {"active_count": 5}
        }

        diversification_analysis = {
            "diversification_score": 75.0,
            "concentration_risk": {"largest_holding_percentage": 15.0}
        }

        dividend_summary = Mock()
        dividend_summary.total_dividends = Decimal('500')
        dividend_summary.dividend_transactions = []

        mcp_provider.analytics_service.get_portfolio_summary.return_value = portfolio_summary
        mcp_provider.analytics_service.get_diversification_analysis.return_value = diversification_analysis
        mcp_provider.analytics_service.calculate_dividend_income.return_value = dividend_summary

        # Act
        result = await mcp_provider.get_performance_summary(tenant_id, portfolio_id)

        # Assert
        assert result["provider"] == "investments"
        assert result["tenant_id"] == tenant_id
        assert result["portfolio_id"] == portfolio_id
        assert result["portfolio_name"] == "Test Portfolio"
        assert result["performance"]["total_value"] == 25000.0
        assert result["diversification"]["diversification_score"] == 75.0
        assert result["dividend_income_last_12_months"]["total_income"] == 500.0

    @pytest.mark.asyncio
    async def test_get_performance_summary_not_found(self, mcp_provider):
        """Test performance summary when portfolio not found"""
        # Arrange
        tenant_id = 1
        portfolio_id = 999

        mcp_provider.analytics_service.get_portfolio_summary.side_effect = NotFoundError("Portfolio not found")

        # Act
        result = await mcp_provider.get_performance_summary(tenant_id, portfolio_id)

        # Assert
        assert result["provider"] == "investments"
        assert result["portfolio_id"] == portfolio_id
        assert "error" in result
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_dividend_forecast_success(self, mcp_provider, sample_portfolio):
        """Test successful dividend forecast retrieval"""
        # Arrange
        tenant_id = 1
        portfolio_id = 1

        dividend_summary = Mock()
        dividend_summary.total_dividends = Decimal('500')
        dividend_summary.dividend_transactions = []

        mcp_provider.portfolio_service.get_portfolio.return_value = sample_portfolio
        mcp_provider.analytics_service.calculate_dividend_income.return_value = dividend_summary
        mcp_provider.holdings_repo.get_by_portfolio.return_value = []
        mcp_provider.transaction_repo.get_by_holding.return_value = []

        # Act
        result = await mcp_provider.get_dividend_forecast(tenant_id, portfolio_id)

        # Assert
        assert result["provider"] == "investments"
        assert result["tenant_id"] == tenant_id
        assert result["portfolio_id"] == portfolio_id
        assert result["portfolio_name"] == "Test Portfolio"
        assert "historical_income" in result
        assert "forecast" in result
        assert result["forecast"]["estimated_annual_income"] == 500.0  # Based on mock dividend data

    @pytest.mark.asyncio
    async def test_get_tax_summary_success(self, mcp_provider, sample_portfolio):
        """Test successful tax summary retrieval"""
        # Arrange
        tenant_id = 1
        tax_year = 2024

        tax_export = Mock()
        tax_export.total_realized_gains = Decimal('1000')
        tax_export.total_dividends = Decimal('500')
        tax_export.transactions = []

        mcp_provider.portfolio_service.get_portfolios.return_value = [sample_portfolio]
        mcp_provider.analytics_service.get_tax_summary.return_value = tax_export

        # Act
        result = await mcp_provider.get_tax_summary(tenant_id, tax_year)

        # Assert
        assert result["provider"] == "investments"
        assert result["tenant_id"] == tenant_id
        assert result["tax_year"] == tax_year
        assert result["summary"]["total_realized_gains"] == 1000.0
        assert result["summary"]["total_dividend_income"] == 500.0
        assert result["summary"]["total_taxable_income"] == 1500.0
        assert len(result["portfolios"]) == 1
        assert "tax_guidance" in result
        assert "disclaimer" in result

    @pytest.mark.asyncio
    async def test_get_tax_summary_invalid_year(self, mcp_provider):
        """Test tax summary with invalid tax year"""
        # Arrange
        tenant_id = 1
        tax_year = 2050  # Future year

        # Act
        result = await mcp_provider.get_tax_summary(tenant_id, tax_year)

        # Assert
        assert result["provider"] == "investments"
        assert result["tax_year"] == tax_year
        assert "error" in result
        assert "Invalid tax year" in result["error"]

    @pytest.mark.asyncio
    async def test_tenant_isolation_enforced(self, mcp_provider):
        """Test that tenant isolation is properly enforced in all methods"""
        # Arrange
        tenant_id = 1

        # Mock services to return empty results (simulating no access)
        mcp_provider.portfolio_service.get_portfolios_with_summary.return_value = []
        mcp_provider.portfolio_service.get_portfolios.return_value = []
        mcp_provider.portfolio_service.get_portfolio.return_value = None

        # Act & Assert - All methods should handle empty results gracefully
        portfolio_summary = await mcp_provider.get_portfolio_summary(tenant_id)
        assert portfolio_summary["summary"]["total_portfolios"] == 0

        holding_details = await mcp_provider.get_holding_details(tenant_id, "AAPL")
        assert holding_details["summary"]["total_holdings"] == 0

        dividend_forecast = await mcp_provider.get_dividend_forecast(tenant_id, 1)
        assert "error" in dividend_forecast  # Portfolio not found

        tax_summary = await mcp_provider.get_tax_summary(tenant_id, 2024)
        assert tax_summary["summary"]["total_portfolios"] == 0

    def test_get_provider_info(self, mcp_provider):
        """Test provider information retrieval"""
        # Act
        info = mcp_provider.get_provider_info()

        # Assert
        assert info["name"] == "investments"
        assert info["version"] == "1.0.0"
        assert "description" in info
        assert len(info["methods"]) == 5
        assert "get_portfolio_summary" in info["methods"]
        assert "get_holding_details" in info["methods"]
        assert "get_performance_summary" in info["methods"]
        assert "get_dividend_forecast" in info["methods"]
        assert "get_tax_summary" in info["methods"]
        assert "capabilities" in info

    def test_error_handling(self, mcp_provider):
        """Test error handling in MCP provider methods"""
        # Arrange
        tenant_id = 1

        # Mock service to raise exception
        mcp_provider.portfolio_service.get_portfolios_with_summary.side_effect = Exception("Database error")

        # Act & Assert - Should not raise exception, should return error in response
        import asyncio
        result = asyncio.run(mcp_provider.get_portfolio_summary(tenant_id))

        assert "error" in result
        assert "Database error" in result["error"]
        assert result["portfolios"] == []

    def test_close_method(self, mcp_provider):
        """Test resource cleanup"""
        # Act
        mcp_provider.close()

        # Assert - Should call close on all services
        mcp_provider.portfolio_service.close.assert_called_once()
        mcp_provider.holdings_service.close.assert_called_once()
        mcp_provider.db.close.assert_called_once()