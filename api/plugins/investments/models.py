"""
Investment Management Database Models

This module defines the SQLAlchemy models for the investment management plugin.
All tables are prefixed with 'investment_' to maintain clear separation from
existing tables and enable easy plugin removal if needed.

The models follow the existing YourFinanceWORKS patterns:
- Use tenant-specific databases (no tenant_id foreign keys)
- Encrypted columns for sensitive data
- Proper relationships and constraints
- Audit fields for tracking
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime, Boolean, Text, Numeric, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, date
from decimal import Decimal
from enum import Enum as PyEnum

# Import encrypted column types for transparent encryption
from core.utils.column_encryptor import EncryptedColumn

# Use the shared Base from the main application for proper test integration
from core.models.models_per_tenant import Base

# Enumerations
class PortfolioType(str, PyEnum):
    """Portfolio types supported by the investment system"""
    TAXABLE = "taxable"
    RETIREMENT = "retirement"  # Generic retirement account
    BUSINESS = "business"

class SecurityType(str, PyEnum):
    """Types of securities that can be held in portfolios"""
    STOCK = "stock"
    BOND = "bond"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    CASH = "cash"

class AssetClass(str, PyEnum):
    """Asset classes for allocation analysis"""
    STOCKS = "stocks"
    BONDS = "bonds"
    CASH = "cash"
    REAL_ESTATE = "real_estate"
    COMMODITIES = "commodities"

class TransactionType(str, PyEnum):
    """Types of investment transactions"""
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    FEE = "fee"
    TRANSFER = "transfer"
    CONTRIBUTION = "contribution"

class DividendType(str, PyEnum):
    """Types of dividends (MVP uses single type)"""
    ORDINARY = "ordinary"  # MVP uses single type


class InvestmentPortfolio(Base):
    """
    Investment portfolio model - represents a collection of investment holdings
    owned by a tenant. Each tenant can have multiple portfolios for different
    account types (taxable, retirement, business).
    """
    __tablename__ = "investment_portfolios"

    id = Column(Integer, primary_key=True, index=True)

    # Tenant isolation
    tenant_id = Column(Integer, nullable=False, index=True)  # For explicit tenant isolation

    # Portfolio identification
    name = Column(EncryptedColumn(), nullable=False, index=True)  # Encrypted for privacy
    portfolio_type = Column(SQLEnum(PortfolioType), nullable=False, index=True)

    # Audit fields
    is_archived = Column(Boolean, default=False, nullable=False)  # Soft delete
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Rebalancing and Targets
    from core.utils.column_encryptor import EncryptedJSON
    target_allocations = Column(EncryptedJSON(), nullable=True)  # Store target weights by AssetClass as JSON

    # Relationships
    holdings = relationship("InvestmentHolding", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("InvestmentTransaction", back_populates="portfolio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<InvestmentPortfolio(id={self.id}, name='{self.name}', type='{self.portfolio_type}')>"


class InvestmentHolding(Base):
    """
    Investment holding model - represents a specific investment position
    (quantity of a security at a cost basis) within a portfolio.
    """
    __tablename__ = "investment_holdings"

    id = Column(Integer, primary_key=True, index=True)

    # Portfolio relationship
    portfolio_id = Column(Integer, ForeignKey("investment_portfolios.id", ondelete="CASCADE"), nullable=False, index=True)

    # Security identification
    security_symbol = Column(String(20), nullable=False, index=True)  # e.g., "AAPL", "VTSAX"
    security_name = Column(EncryptedColumn(), nullable=True)  # Encrypted for privacy
    security_type = Column(SQLEnum(SecurityType), nullable=False, index=True)
    asset_class = Column(SQLEnum(AssetClass), nullable=False, index=True)

    # Position data
    quantity = Column(Numeric(precision=18, scale=8), nullable=False)  # High precision for fractional shares
    cost_basis = Column(Numeric(precision=18, scale=2), nullable=False)  # Total cost basis for all shares
    purchase_date = Column(Date, nullable=False)  # Initial purchase date for the holding

    # Current pricing
    current_price = Column(Numeric(precision=18, scale=2), nullable=True)  # Current price per share
    price_updated_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_closed = Column(Boolean, default=False, nullable=False)  # True when quantity reaches zero

    # Audit fields
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    portfolio = relationship("InvestmentPortfolio", back_populates="holdings")
    transactions = relationship("InvestmentTransaction", back_populates="holding", cascade="all, delete-orphan")

    @property
    def average_cost_per_share(self) -> Decimal:
        """Calculate average cost per share"""
        if self.quantity and self.quantity > 0:
            return Decimal(str(self.cost_basis)) / Decimal(str(self.quantity))
        return Decimal('0')

    @property
    def current_value(self) -> Decimal:
        """Calculate current market value of the holding"""
        if self.current_price and self.quantity:
            return Decimal(str(self.current_price)) * Decimal(str(self.quantity))
        # Fallback to cost basis if no current price
        return Decimal(str(self.cost_basis)) if self.cost_basis else Decimal('0')

    @property
    def unrealized_gain_loss(self) -> Decimal:
        """Calculate unrealized gain/loss"""
        return self.current_value - Decimal(str(self.cost_basis))

    def __repr__(self):
        return f"<InvestmentHolding(id={self.id}, symbol='{self.security_symbol}', quantity={self.quantity})>"


class InvestmentTransaction(Base):
    """
    Investment transaction model - represents all investment activities
    (buy, sell, dividend, etc.) that affect holdings or generate income.
    """
    __tablename__ = "investment_transactions"

    id = Column(Integer, primary_key=True, index=True)

    # Portfolio and holding relationships
    portfolio_id = Column(Integer, ForeignKey("investment_portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    holding_id = Column(Integer, ForeignKey("investment_holdings.id", ondelete="CASCADE"), nullable=True, index=True)  # Nullable for cash transactions

    # Transaction details
    transaction_type = Column(SQLEnum(TransactionType), nullable=False, index=True)
    transaction_date = Column(Date, nullable=False, index=True)

    # Financial data
    quantity = Column(Numeric(precision=18, scale=8), nullable=True)  # Nullable for dividends, fees, etc.
    price_per_share = Column(Numeric(precision=18, scale=2), nullable=True)  # Nullable for dividends, fees, etc.
    total_amount = Column(Numeric(precision=18, scale=2), nullable=False)  # Always required
    fees = Column(Numeric(precision=18, scale=2), default=0, nullable=False)

    # Calculated fields
    realized_gain = Column(Numeric(precision=18, scale=2), nullable=True)  # For SELL transactions (simple average cost basis)

    # Dividend-specific fields
    dividend_type = Column(SQLEnum(DividendType), nullable=True)  # For DIVIDEND transactions
    payment_date = Column(Date, nullable=True)  # For DIVIDEND transactions (when dividend was paid)
    ex_dividend_date = Column(Date, nullable=True)  # For DIVIDEND transactions (ex-dividend date)

    # Additional information
    notes = Column(EncryptedColumn(), nullable=True)  # Encrypted for privacy

    # Audit fields
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    portfolio = relationship("InvestmentPortfolio", back_populates="transactions")
    holding = relationship("InvestmentHolding", back_populates="transactions")

    def __repr__(self):
        return f"<InvestmentTransaction(id={self.id}, type='{self.transaction_type}', amount={self.total_amount})>"

    # Constraints
    __table_args__ = (
        # Ensure dividend transactions have dividend_type
        # Note: SQLAlchemy check constraints are database-specific, so we'll handle this in validation
    )


# Index definitions for performance
# These will be created by the migration script

# Indexes for common queries:
# - investment_portfolios: portfolio_type, created_at
# - investment_holdings: portfolio_id, security_symbol, asset_class, is_closed
# - investment_transactions: portfolio_id, transaction_date, transaction_type, holding_id