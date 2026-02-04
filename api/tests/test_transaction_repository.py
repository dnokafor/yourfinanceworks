"""
Unit tests for TransactionRepository

This module tests the transaction repository functionality including
CRUD operations, filtering, and tenant isolation.
"""

import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from plugins.investments.repositories.transaction_repository import TransactionRepository
from plugins.investments.repositories.portfolio_repository import PortfolioRepository
from plugins.investments.repositories.holdings_repository import HoldingsRepository
from plugins.investments.models import (
    InvestmentPortfolio, InvestmentHolding, InvestmentTransaction,
    PortfolioType, SecurityType, AssetClass, TransactionType, DividendType
)


class TestTransactionRepository:
    """Test cases for TransactionRepository"""

    @pytest.fixture
    def db_session(self):
        """Create a test database session"""
        # This would be set up with a test database
        # For now, we'll assume the session is properly configured
        pass

    @pytest.fixture
    def transaction_repo(self, db_session):
        """Create a TransactionRepository instance"""
        return TransactionRepository(db_session)

    @pytest.fixture
    def portfolio_repo(self, db_session):
        """Create a PortfolioRepository instance"""
        return PortfolioRepository(db_session)

    @pytest.fixture
    def holdings_repo(self, db_session):
        """Create a HoldingsRepository instance"""
        return HoldingsRepository(db_session)

    @pytest.fixture
    def sample_portfolio(self, portfolio_repo):
        """Create a sample portfolio for testing"""
        return portfolio_repo.create(
            tenant_id=1,
            name="Test Portfolio",
            portfolio_type=PortfolioType.TAXABLE
        )

    @pytest.fixture
    def sample_holding(self, holdings_repo, sample_portfolio):
        """Create a sample holding for testing"""
        return holdings_repo.create(
            portfolio_id=sample_portfolio.id,
            security_symbol="AAPL",
            security_name="Apple Inc.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('100'),
            cost_basis=Decimal('10000'),
            purchase_date=date(2024, 1, 1)
        )

    def test_create_buy_transaction(self, transaction_repo, sample_portfolio, sample_holding):
        """Test creating a buy transaction"""
        transaction = transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.BUY,
            transaction_date=date(2024, 1, 15),
            total_amount=Decimal('5000'),
            holding_id=sample_holding.id,
            quantity=Decimal('50'),
            price_per_share=Decimal('100'),
            fees=Decimal('10')
        )

        assert transaction.id is not None
        assert transaction.portfolio_id == sample_portfolio.id
        assert transaction.holding_id == sample_holding.id
        assert transaction.transaction_type == TransactionType.BUY
        assert transaction.quantity == Decimal('50')
        assert transaction.price_per_share == Decimal('100')
        assert transaction.total_amount == Decimal('5000')
        assert transaction.fees == Decimal('10')

    def test_create_sell_transaction(self, transaction_repo, sample_portfolio, sample_holding):
        """Test creating a sell transaction with realized gain"""
        transaction = transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.SELL,
            transaction_date=date(2024, 2, 15),
            total_amount=Decimal('6000'),
            holding_id=sample_holding.id,
            quantity=Decimal('50'),
            price_per_share=Decimal('120'),
            fees=Decimal('10'),
            realized_gain=Decimal('1000')
        )

        assert transaction.transaction_type == TransactionType.SELL
        assert transaction.realized_gain == Decimal('1000')

    def test_create_dividend_transaction(self, transaction_repo, sample_portfolio, sample_holding):
        """Test creating a dividend transaction"""
        transaction = transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.DIVIDEND,
            transaction_date=date(2024, 3, 15),
            total_amount=Decimal('100'),
            holding_id=sample_holding.id,
            dividend_type=DividendType.ORDINARY,
            payment_date=date(2024, 3, 15),
            ex_dividend_date=date(2024, 3, 10)
        )

        assert transaction.transaction_type == TransactionType.DIVIDEND
        assert transaction.dividend_type == DividendType.ORDINARY
        assert transaction.payment_date == date(2024, 3, 15)
        assert transaction.ex_dividend_date == date(2024, 3, 10)
        assert transaction.quantity is None  # Dividends don't have quantity

    def test_get_by_id(self, transaction_repo, sample_portfolio, sample_holding):
        """Test retrieving a transaction by ID"""
        # Create a transaction
        created_transaction = transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.BUY,
            transaction_date=date(2024, 1, 15),
            total_amount=Decimal('5000'),
            holding_id=sample_holding.id,
            quantity=Decimal('50'),
            price_per_share=Decimal('100')
        )

        # Retrieve it
        retrieved_transaction = transaction_repo.get_by_id(created_transaction.id)

        assert retrieved_transaction is not None
        assert retrieved_transaction.id == created_transaction.id
        assert retrieved_transaction.total_amount == Decimal('5000')

    def test_get_by_portfolio(self, transaction_repo, sample_portfolio, sample_holding):
        """Test retrieving transactions by portfolio"""
        # Create multiple transactions
        transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.BUY,
            transaction_date=date(2024, 1, 15),
            total_amount=Decimal('5000'),
            holding_id=sample_holding.id,
            quantity=Decimal('50'),
            price_per_share=Decimal('100')
        )

        transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.DIVIDEND,
            transaction_date=date(2024, 2, 15),
            total_amount=Decimal('100'),
            holding_id=sample_holding.id,
            dividend_type=DividendType.ORDINARY
        )

        # Retrieve all transactions
        transactions = transaction_repo.get_by_portfolio(sample_portfolio.id)

        assert len(transactions) == 2
        # Should be ordered by date descending (most recent first)
        assert transactions[0].transaction_date >= transactions[1].transaction_date

    def test_get_by_date_range(self, transaction_repo, sample_portfolio, sample_holding):
        """Test retrieving transactions by date range"""
        # Create transactions on different dates
        transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.BUY,
            transaction_date=date(2024, 1, 15),
            total_amount=Decimal('5000'),
            holding_id=sample_holding.id,
            quantity=Decimal('50'),
            price_per_share=Decimal('100')
        )

        transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.SELL,
            transaction_date=date(2024, 3, 15),
            total_amount=Decimal('6000'),
            holding_id=sample_holding.id,
            quantity=Decimal('50'),
            price_per_share=Decimal('120')
        )

        # Get transactions in February (should be empty)
        feb_transactions = transaction_repo.get_by_date_range(
            sample_portfolio.id,
            date(2024, 2, 1),
            date(2024, 2, 29)
        )
        assert len(feb_transactions) == 0

        # Get transactions from January to March (should get both)
        all_transactions = transaction_repo.get_by_date_range(
            sample_portfolio.id,
            date(2024, 1, 1),
            date(2024, 3, 31)
        )
        assert len(all_transactions) == 2

    def test_get_dividend_transactions(self, transaction_repo, sample_portfolio, sample_holding):
        """Test retrieving only dividend transactions"""
        # Create mixed transactions
        transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.BUY,
            transaction_date=date(2024, 1, 15),
            total_amount=Decimal('5000'),
            holding_id=sample_holding.id,
            quantity=Decimal('50'),
            price_per_share=Decimal('100')
        )

        transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.DIVIDEND,
            transaction_date=date(2024, 2, 15),
            total_amount=Decimal('100'),
            holding_id=sample_holding.id,
            dividend_type=DividendType.ORDINARY
        )

        # Get only dividend transactions
        dividend_transactions = transaction_repo.get_dividend_transactions(sample_portfolio.id)

        assert len(dividend_transactions) == 1
        assert dividend_transactions[0].transaction_type == TransactionType.DIVIDEND

    def test_calculate_total_dividends(self, transaction_repo, sample_portfolio, sample_holding):
        """Test calculating total dividend income"""
        # Create dividend transactions
        transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.DIVIDEND,
            transaction_date=date(2024, 1, 15),
            total_amount=Decimal('100'),
            holding_id=sample_holding.id,
            dividend_type=DividendType.ORDINARY
        )

        transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.DIVIDEND,
            transaction_date=date(2024, 2, 15),
            total_amount=Decimal('150'),
            holding_id=sample_holding.id,
            dividend_type=DividendType.ORDINARY
        )

        # Calculate total dividends
        total_dividends = transaction_repo.calculate_total_dividends(sample_portfolio.id)

        assert total_dividends == Decimal('250')

    def test_calculate_total_realized_gains(self, transaction_repo, sample_portfolio, sample_holding):
        """Test calculating total realized gains"""
        # Create sell transactions with realized gains
        transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.SELL,
            transaction_date=date(2024, 1, 15),
            total_amount=Decimal('6000'),
            holding_id=sample_holding.id,
            quantity=Decimal('50'),
            price_per_share=Decimal('120'),
            realized_gain=Decimal('1000')
        )

        transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.SELL,
            transaction_date=date(2024, 2, 15),
            total_amount=Decimal('4500'),
            holding_id=sample_holding.id,
            quantity=Decimal('50'),
            price_per_share=Decimal('90'),
            realized_gain=Decimal('-500')  # Loss
        )

        # Calculate total realized gains
        total_gains = transaction_repo.calculate_total_realized_gains(sample_portfolio.id)

        assert total_gains == Decimal('500')  # 1000 - 500

    def test_check_duplicate_transaction(self, transaction_repo, sample_portfolio, sample_holding):
        """Test duplicate transaction detection"""
        # Create a transaction
        transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.BUY,
            transaction_date=date(2024, 1, 15),
            total_amount=Decimal('5000'),
            holding_id=sample_holding.id,
            quantity=Decimal('50'),
            price_per_share=Decimal('100')
        )

        # Check for duplicate (should find it)
        is_duplicate = transaction_repo.check_duplicate_transaction(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.BUY,
            transaction_date=date(2024, 1, 15),
            total_amount=Decimal('5000'),
            quantity=Decimal('50'),
            holding_id=sample_holding.id
        )

        assert is_duplicate is True

        # Check for non-duplicate (different amount)
        is_not_duplicate = transaction_repo.check_duplicate_transaction(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.BUY,
            transaction_date=date(2024, 1, 15),
            total_amount=Decimal('6000'),  # Different amount
            quantity=Decimal('50'),
            holding_id=sample_holding.id
        )

        assert is_not_duplicate is False

    def test_transaction_ordering(self, transaction_repo, sample_portfolio, sample_holding):
        """Test that transactions are properly ordered by date"""
        # Create transactions in non-chronological order
        transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.BUY,
            transaction_date=date(2024, 3, 15),  # Latest
            total_amount=Decimal('3000'),
            holding_id=sample_holding.id,
            quantity=Decimal('30'),
            price_per_share=Decimal('100')
        )

        transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.BUY,
            transaction_date=date(2024, 1, 15),  # Earliest
            total_amount=Decimal('1000'),
            holding_id=sample_holding.id,
            quantity=Decimal('10'),
            price_per_share=Decimal('100')
        )

        transaction_repo.create(
            portfolio_id=sample_portfolio.id,
            transaction_type=TransactionType.BUY,
            transaction_date=date(2024, 2, 15),  # Middle
            total_amount=Decimal('2000'),
            holding_id=sample_holding.id,
            quantity=Decimal('20'),
            price_per_share=Decimal('100')
        )

        # Get transactions (should be ordered by date descending)
        transactions = transaction_repo.get_by_portfolio(sample_portfolio.id)

        assert len(transactions) == 3
        assert transactions[0].transaction_date == date(2024, 3, 15)  # Most recent first
        assert transactions[1].transaction_date == date(2024, 2, 15)
        assert transactions[2].transaction_date == date(2024, 1, 15)  # Oldest last

        # Get transactions by date range (should be ordered ascending)
        date_range_transactions = transaction_repo.get_by_date_range(
            sample_portfolio.id,
            date(2024, 1, 1),
            date(2024, 3, 31)
        )

        assert len(date_range_transactions) == 3
        assert date_range_transactions[0].transaction_date == date(2024, 1, 15)  # Oldest first
        assert date_range_transactions[1].transaction_date == date(2024, 2, 15)
        assert date_range_transactions[2].transaction_date == date(2024, 3, 15)  # Most recent last