"""
Unit tests for Investment Transaction Service

This module tests the TransactionService class to ensure proper business logic,
validation, and integration with repositories for all transaction types.
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone, date
from decimal import Decimal

# Import investment models and service
from plugins.investments.models import (
    InvestmentPortfolio,
    InvestmentHolding,
    InvestmentTransaction,
    PortfolioType,
    SecurityType,
    AssetClass,
    TransactionType,
    DividendType,
    Base as InvestmentBase
)
from plugins.investments.services.transaction_service import TransactionService
from plugins.investments.schemas import TransactionResponse
from core.exceptions.base import ValidationError, NotFoundError, ConflictError


class TestTransactionService:
    """Test suite for TransactionService"""

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
    def transaction_service(self, investment_db_session):
        """Create TransactionService instance with test database session"""
        return TransactionService(investment_db_session)

    @pytest.fixture
    def sample_portfolio(self, investment_db_session):
        """Create a sample portfolio for testing"""
        portfolio = InvestmentPortfolio(
            tenant_id=1,  # Add tenant_id for proper tenant isolation
            name="Test Portfolio",
            portfolio_type=PortfolioType.TAXABLE,
            is_archived=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        investment_db_session.add(portfolio)
        investment_db_session.commit()
        investment_db_session.refresh(portfolio)
        return portfolio

    @pytest.fixture
    def sample_holding(self, investment_db_session, sample_portfolio):
        """Create a sample holding for testing"""
        holding = InvestmentHolding(
            portfolio_id=sample_portfolio.id,
            security_symbol="AAPL",
            security_name="Apple Inc.",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('100'),
            cost_basis=Decimal('10000'),  # $100 per share
            purchase_date=date(2024, 1, 1),
            current_price=Decimal('150'),
            is_closed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        investment_db_session.add(holding)
        investment_db_session.commit()
        investment_db_session.refresh(holding)
        return holding

    def test_record_transaction_buy_success(self, transaction_service, investment_db_session, sample_portfolio, sample_holding):
        """Test successful buy transaction recording"""
        # Arrange
        tenant_id = 1
        transaction_data = {
            'transaction_type': TransactionType.BUY,
            'transaction_date': date(2024, 2, 1),
            'holding_id': sample_holding.id,
            'quantity': Decimal('50'),
            'price_per_share': Decimal('120'),
            'total_amount': Decimal('6000'),
            'fees': Decimal('10'),
            'notes': 'Additional purchase'
        }

        # Act
        result = transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)

        # Assert
        assert isinstance(result, TransactionResponse)
        assert result.transaction_type == TransactionType.BUY
        assert result.quantity == Decimal('50')
        assert result.price_per_share == Decimal('120')
        assert result.total_amount == Decimal('6000')
        assert result.fees == Decimal('10')

        # Verify holding was updated
        updated_holding = investment_db_session.query(InvestmentHolding).filter_by(id=sample_holding.id).first()
        assert updated_holding.quantity == Decimal('150')  # 100 + 50
        assert updated_holding.cost_basis == Decimal('16010')  # 10000 + 6000 + 10

    def test_record_transaction_sell_success(self, transaction_service, investment_db_session, sample_portfolio, sample_holding):
        """Test successful sell transaction recording"""
        # Arrange
        tenant_id = 1
        transaction_data = {
            'transaction_type': TransactionType.SELL,
            'transaction_date': date(2024, 2, 1),
            'holding_id': sample_holding.id,
            'quantity': Decimal('25'),
            'price_per_share': Decimal('150'),
            'total_amount': Decimal('3750'),
            'fees': Decimal('5'),
            'notes': 'Partial sale'
        }

        # Act
        result = transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)

        # Assert
        assert isinstance(result, TransactionResponse)
        assert result.transaction_type == TransactionType.SELL
        assert result.quantity == Decimal('25')
        assert result.price_per_share == Decimal('150')
        assert result.total_amount == Decimal('3750')
        assert result.fees == Decimal('5')
        assert result.realized_gain is not None

        # Calculate expected realized gain: (25 * 150 - 5) - (25 * 100) = 3745 - 2500 = 1245
        expected_gain = Decimal('1245')
        assert result.realized_gain == expected_gain

        # Verify holding was updated
        updated_holding = investment_db_session.query(InvestmentHolding).filter_by(id=sample_holding.id).first()
        assert updated_holding.quantity == Decimal('75')  # 100 - 25
        assert updated_holding.cost_basis == Decimal('7500')  # 10000 - 2500

    def test_record_transaction_sell_insufficient_quantity(self, transaction_service, sample_portfolio, sample_holding):
        """Test sell transaction with insufficient quantity"""
        # Arrange
        tenant_id = 1
        transaction_data = {
            'transaction_type': TransactionType.SELL,
            'transaction_date': date(2024, 2, 1),
            'holding_id': sample_holding.id,
            'quantity': Decimal('150'),  # More than available (100)
            'price_per_share': Decimal('150'),
            'total_amount': Decimal('22500'),
            'fees': Decimal('5')
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="Insufficient quantity"):
            transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)

    def test_record_transaction_dividend_success(self, transaction_service, investment_db_session, sample_portfolio, sample_holding):
        """Test successful dividend transaction recording"""
        # Arrange
        tenant_id = 1
        transaction_data = {
            'transaction_type': TransactionType.DIVIDEND,
            'transaction_date': date(2024, 2, 1),
            'holding_id': sample_holding.id,
            'total_amount': Decimal('100'),
            'dividend_type': DividendType.ORDINARY,
            'payment_date': date(2024, 2, 1),
            'ex_dividend_date': date(2024, 1, 28),
            'notes': 'Quarterly dividend'
        }

        # Act
        result = transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)

        # Assert
        assert isinstance(result, TransactionResponse)
        assert result.transaction_type == TransactionType.DIVIDEND
        assert result.total_amount == Decimal('100')
        assert result.dividend_type == DividendType.ORDINARY
        assert result.payment_date == date(2024, 2, 1)
        assert result.ex_dividend_date == date(2024, 1, 28)

        # Verify holding quantity unchanged
        updated_holding = investment_db_session.query(InvestmentHolding).filter_by(id=sample_holding.id).first()
        assert updated_holding.quantity == Decimal('100')  # Unchanged
        assert updated_holding.cost_basis == Decimal('10000')  # Unchanged

    def test_record_transaction_interest_success(self, transaction_service, sample_portfolio):
        """Test successful interest transaction recording"""
        # Arrange
        tenant_id = 1
        transaction_data = {
            'transaction_type': TransactionType.INTEREST,
            'transaction_date': date(2024, 2, 1),
            'total_amount': Decimal('50'),
            'notes': 'Cash interest'
        }

        # Act
        result = transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)

        # Assert
        assert isinstance(result, TransactionResponse)
        assert result.transaction_type == TransactionType.INTEREST
        assert result.total_amount == Decimal('50')
        assert result.holding_id is None  # Cash transaction

    def test_record_transaction_fee_success(self, transaction_service, sample_portfolio):
        """Test successful fee transaction recording"""
        # Arrange
        tenant_id = 1
        transaction_data = {
            'transaction_type': TransactionType.FEE,
            'transaction_date': date(2024, 2, 1),
            'total_amount': Decimal('-25'),  # Negative for fee charge
            'notes': 'Account maintenance fee'
        }

        # Act
        result = transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)

        # Assert
        assert isinstance(result, TransactionResponse)
        assert result.transaction_type == TransactionType.FEE
        assert result.total_amount == Decimal('-25')

    def test_record_transaction_transfer_success(self, transaction_service, sample_portfolio):
        """Test successful transfer transaction recording"""
        # Arrange
        tenant_id = 1
        transaction_data = {
            'transaction_type': TransactionType.TRANSFER,
            'transaction_date': date(2024, 2, 1),
            'total_amount': Decimal('1000'),
            'notes': 'Cash transfer in'
        }

        # Act
        result = transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)

        # Assert
        assert isinstance(result, TransactionResponse)
        assert result.transaction_type == TransactionType.TRANSFER
        assert result.total_amount == Decimal('1000')

    def test_record_transaction_contribution_success(self, transaction_service, sample_portfolio):
        """Test successful contribution transaction recording"""
        # Arrange
        tenant_id = 1
        transaction_data = {
            'transaction_type': TransactionType.CONTRIBUTION,
            'transaction_date': date(2024, 2, 1),
            'total_amount': Decimal('5000'),
            'notes': 'Annual contribution'
        }

        # Act
        result = transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)

        # Assert
        assert isinstance(result, TransactionResponse)
        assert result.transaction_type == TransactionType.CONTRIBUTION
        assert result.total_amount == Decimal('5000')

    def test_record_transaction_missing_required_fields(self, transaction_service, sample_portfolio):
        """Test transaction recording with missing required fields"""
        # Arrange
        tenant_id = 1
        transaction_data = {
            'transaction_type': TransactionType.BUY,
            # Missing transaction_date and total_amount
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="Required field"):
            transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)

    def test_record_transaction_future_date(self, transaction_service, sample_portfolio):
        """Test transaction recording with future date"""
        # Arrange
        tenant_id = 1
        future_date = date(2030, 1, 1)
        transaction_data = {
            'transaction_type': TransactionType.INTEREST,
            'transaction_date': future_date,
            'total_amount': Decimal('50')
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="Transaction date cannot be in the future"):
            transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)

    def test_record_transaction_negative_amount_for_buy(self, transaction_service, sample_portfolio, sample_holding):
        """Test buy transaction with negative amount"""
        # Arrange
        tenant_id = 1
        transaction_data = {
            'transaction_type': TransactionType.BUY,
            'transaction_date': date(2024, 2, 1),
            'holding_id': sample_holding.id,
            'quantity': Decimal('50'),
            'price_per_share': Decimal('120'),
            'total_amount': Decimal('-6000'),  # Negative amount
            'fees': Decimal('10')
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="Amount must be positive"):
            transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)

    def test_record_transaction_zero_amount_for_fee(self, transaction_service, sample_portfolio):
        """Test fee transaction with zero amount"""
        # Arrange
        tenant_id = 1
        transaction_data = {
            'transaction_type': TransactionType.FEE,
            'transaction_date': date(2024, 2, 1),
            'total_amount': Decimal('0')  # Zero amount not allowed for fees
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="Amount cannot be zero"):
            transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)

    def test_record_transaction_portfolio_not_found(self, transaction_service):
        """Test transaction recording with non-existent portfolio"""
        # Arrange
        tenant_id = 1
        portfolio_id = 999  # Non-existent
        transaction_data = {
            'transaction_type': TransactionType.INTEREST,
            'transaction_date': date(2024, 2, 1),
            'total_amount': Decimal('50')
        }

        # Act & Assert
        with pytest.raises(NotFoundError, match="Portfolio 999 not found"):
            transaction_service.record_transaction(tenant_id, portfolio_id, transaction_data)

    def test_record_transaction_holding_not_found(self, transaction_service, sample_portfolio):
        """Test transaction recording with non-existent holding"""
        # Arrange
        tenant_id = 1
        transaction_data = {
            'transaction_type': TransactionType.BUY,
            'transaction_date': date(2024, 2, 1),
            'holding_id': 999,  # Non-existent
            'quantity': Decimal('50'),
            'price_per_share': Decimal('120'),
            'total_amount': Decimal('6000')
        }

        # Act & Assert
        with pytest.raises(NotFoundError, match="Holding 999 not found"):
            transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)

    def test_calculate_realized_gain_simple_average_cost(self, transaction_service, sample_holding):
        """Test realized gain calculation using simple average cost"""
        # Arrange
        sell_quantity = Decimal('25')
        sell_price = Decimal('150')
        fees = Decimal('5')

        # Act
        realized_gain = transaction_service.calculate_realized_gain(sample_holding, sell_quantity, sell_price, fees)

        # Assert
        # Average cost per share: 10000 / 100 = 100
        # Cost basis for 25 shares: 25 * 100 = 2500
        # Gross proceeds: 25 * 150 = 3750
        # Net proceeds: 3750 - 5 = 3745
        # Realized gain: 3745 - 2500 = 1245
        expected_gain = Decimal('1245')
        assert realized_gain == expected_gain

    def test_calculate_realized_gain_zero_quantity_holding(self, transaction_service):
        """Test realized gain calculation with zero quantity holding"""
        # Arrange
        holding = InvestmentHolding(
            portfolio_id=1,
            security_symbol="TEST",
            security_name="Test Stock",
            security_type=SecurityType.STOCK,
            asset_class=AssetClass.STOCKS,
            quantity=Decimal('0'),  # Zero quantity
            cost_basis=Decimal('0'),
            purchase_date=date(2024, 1, 1)
        )

        # Act & Assert
        with pytest.raises(ValidationError, match="Cannot calculate realized gain for holding with zero quantity"):
            transaction_service.calculate_realized_gain(holding, Decimal('10'), Decimal('100'))

    def test_get_transactions_success(self, transaction_service, investment_db_session, sample_portfolio, sample_holding):
        """Test getting transactions for a portfolio"""
        # Arrange
        tenant_id = 1

        # Create some test transactions
        transaction1 = InvestmentTransaction(
            portfolio_id=sample_portfolio.id,
            holding_id=sample_holding.id,
            transaction_type=TransactionType.BUY,
            transaction_date=date(2024, 1, 1),
            quantity=Decimal('100'),
            price_per_share=Decimal('100'),
            total_amount=Decimal('10000'),
            fees=Decimal('0'),
            created_at=datetime.now(timezone.utc)
        )

        transaction2 = InvestmentTransaction(
            portfolio_id=sample_portfolio.id,
            holding_id=sample_holding.id,
            transaction_type=TransactionType.DIVIDEND,
            transaction_date=date(2024, 2, 1),
            total_amount=Decimal('100'),
            dividend_type=DividendType.ORDINARY,
            created_at=datetime.now(timezone.utc)
        )

        investment_db_session.add_all([transaction1, transaction2])
        investment_db_session.commit()

        # Act
        transactions = transaction_service.get_transactions(tenant_id, sample_portfolio.id)

        # Assert
        assert len(transactions) == 2
        assert all(isinstance(t, TransactionResponse) for t in transactions)

        # Should be ordered by date descending
        assert transactions[0].transaction_date >= transactions[1].transaction_date

    def test_get_transactions_with_filters(self, transaction_service, investment_db_session, sample_portfolio, sample_holding):
        """Test getting transactions with date and type filters"""
        # Arrange
        tenant_id = 1

        # Create test transactions with different dates and types
        transaction1 = InvestmentTransaction(
            portfolio_id=sample_portfolio.id,
            holding_id=sample_holding.id,
            transaction_type=TransactionType.BUY,
            transaction_date=date(2024, 1, 1),
            quantity=Decimal('100'),
            price_per_share=Decimal('100'),
            total_amount=Decimal('10000'),
            created_at=datetime.now(timezone.utc)
        )

        transaction2 = InvestmentTransaction(
            portfolio_id=sample_portfolio.id,
            holding_id=sample_holding.id,
            transaction_type=TransactionType.DIVIDEND,
            transaction_date=date(2024, 2, 1),
            total_amount=Decimal('100'),
            dividend_type=DividendType.ORDINARY,
            created_at=datetime.now(timezone.utc)
        )

        investment_db_session.add_all([transaction1, transaction2])
        investment_db_session.commit()

        # Act - filter by transaction type
        dividend_transactions = transaction_service.get_transactions(
            tenant_id,
            sample_portfolio.id,
            transaction_types=[TransactionType.DIVIDEND]
        )

        # Assert
        assert len(dividend_transactions) == 1
        assert dividend_transactions[0].transaction_type == TransactionType.DIVIDEND

    def test_get_transaction_success(self, transaction_service, investment_db_session, sample_portfolio, sample_holding):
        """Test getting a specific transaction by ID"""
        # Arrange
        tenant_id = 1

        transaction = InvestmentTransaction(
            portfolio_id=sample_portfolio.id,
            holding_id=sample_holding.id,
            transaction_type=TransactionType.BUY,
            transaction_date=date(2024, 1, 1),
            quantity=Decimal('100'),
            price_per_share=Decimal('100'),
            total_amount=Decimal('10000'),
            created_at=datetime.now(timezone.utc)
        )

        investment_db_session.add(transaction)
        investment_db_session.commit()
        investment_db_session.refresh(transaction)

        # Act
        result = transaction_service.get_transaction(tenant_id, transaction.id)

        # Assert
        assert isinstance(result, TransactionResponse)
        assert result.id == transaction.id
        assert result.transaction_type == TransactionType.BUY

    def test_get_transaction_not_found(self, transaction_service):
        """Test getting non-existent transaction"""
        # Arrange
        tenant_id = 1
        transaction_id = 999

        # Act & Assert
        with pytest.raises(NotFoundError, match="Transaction 999 not found"):
            transaction_service.get_transaction(tenant_id, transaction_id)

    def test_duplicate_transaction_detection(self, transaction_service, investment_db_session, sample_portfolio, sample_holding):
        """Test duplicate transaction detection within time window"""
        # Arrange
        tenant_id = 1
        transaction_data = {
            'transaction_type': TransactionType.BUY,
            'transaction_date': date(2024, 2, 1),
            'holding_id': sample_holding.id,
            'quantity': Decimal('50'),
            'price_per_share': Decimal('120'),
            'total_amount': Decimal('6000'),
            'fees': Decimal('10')
        }

        # Act - Record first transaction
        transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)

        # Act & Assert - Try to record identical transaction
        with pytest.raises(ConflictError, match="Duplicate transaction detected"):
            transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)

    def test_unsupported_transaction_type(self, transaction_service, sample_portfolio):
        """Test recording transaction with unsupported type"""
        # Arrange
        tenant_id = 1
        transaction_data = {
            'transaction_type': 'UNSUPPORTED',  # Invalid type
            'transaction_date': date(2024, 2, 1),
            'total_amount': Decimal('100')
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="Unsupported transaction type"):
            transaction_service.record_transaction(tenant_id, sample_portfolio.id, transaction_data)