"""
Investment Management API Router

This module defines the FastAPI router for investment management endpoints.
All routes are protected by commercial license requirements and tenant isolation.
Comprehensive error handling ensures consistent error responses across all endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError as PydanticValidationError

# Import core dependencies
from core.models.database import get_db
from core.routers.auth import get_current_user
from core.models.models import MasterUser
from core.utils.feature_gate import require_feature

# Import schemas
from .schemas import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse,
    HoldingCreate, HoldingUpdate, HoldingResponse, PriceUpdate,
    BuyTransactionCreate, SellTransactionCreate, DividendTransactionCreate,
    OtherTransactionCreate, TransactionResponse,
    PerformanceMetrics, AssetAllocation, DividendSummary, TaxExport,
    DateRangeQuery, TaxYearQuery, ErrorResponse
)

# Import models for enums
from .models import PortfolioType

# Import services
from .services.portfolio_service import PortfolioService
from .services.holdings_service import HoldingsService
from .services.transaction_service import TransactionService
from .services.analytics_service import AnalyticsService

# Import error handling
from .exceptions import (
    InvestmentError, ValidationError, TenantAccessError, ResourceNotFoundError,
    ConflictError, DuplicateTransactionError
)
from .error_handlers import (
    handle_investment_error, handle_pydantic_validation_error,
    handle_sqlalchemy_error, handle_generic_exception,
    raise_not_found_error, raise_tenant_access_error
)
from .validation import (
    PortfolioValidator, HoldingValidator, TransactionValidator,
    DuplicateTransactionDetector
)

# Import validation middleware
from .middleware import (
    ValidationMiddleware, RequestValidationMiddleware,
    validate_portfolio_id_param, validate_holding_id_param,
    validate_transaction_id_param, validate_tax_year_param,
    validate_date_range_params, validate_pagination_params
)

# Investment router
investment_router = APIRouter()

# Note: Exception handlers are handled at the application level, not router level
# Individual endpoints will handle errors using try/catch blocks and return appropriate responses

# Placeholder endpoints - will be implemented in later tasks
@investment_router.get("/health")
async def health_check():
    """Health check endpoint for investment plugin"""
    return {"status": "ok", "plugin": "investment-management", "version": "1.0.0"}

# Portfolio endpoints
@investment_router.post("/portfolios", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
@require_feature("investments")
async def create_portfolio(
    portfolio: PortfolioCreate,
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new investment portfolio"""
    try:
        # Validate and normalize input data
        validated_data = RequestValidationMiddleware.validate_portfolio_create_request(portfolio.dict())

        service = PortfolioService(db)
        created_portfolio = service.create_portfolio(
            tenant_id=current_user.tenant_id,
            portfolio_data=validated_data
        )
        return PortfolioResponse.model_validate(created_portfolio)
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to create portfolio: {str(e)}")

@investment_router.get("/portfolios", response_model=List[PortfolioResponse])
@require_feature("investments")
async def get_portfolios(
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_archived: bool = False
):
    """Get all portfolios for the current tenant"""
    try:
        service = PortfolioService(db)
        portfolios = service.get_portfolios(
            tenant_id=current_user.tenant_id,
            include_archived=include_archived
        )
        return [PortfolioResponse.model_validate(p) for p in portfolios]
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to retrieve portfolios: {str(e)}")

@investment_router.get("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
@require_feature("investments")
async def get_portfolio(
    portfolio_id: int = Depends(validate_portfolio_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific portfolio"""
    try:
        service = PortfolioService(db)

        # Validate tenant access
        if not service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        portfolio = service.get_portfolio(
            portfolio_id=portfolio_id,
            tenant_id=current_user.tenant_id
        )
        if not portfolio:
            raise_not_found_error("Portfolio", portfolio_id)

        return PortfolioResponse.model_validate(portfolio)
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to retrieve portfolio: {str(e)}")

@investment_router.put("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
@require_feature("investments")
async def update_portfolio(
    portfolio: PortfolioUpdate,
    portfolio_id: int = Depends(validate_portfolio_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a portfolio"""
    try:
        # Validate and normalize input data
        validated_data = RequestValidationMiddleware.validate_portfolio_update_request(
            portfolio.dict(exclude_unset=True)
        )

        service = PortfolioService(db)

        # Validate tenant access
        if not service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        updated_portfolio = service.update_portfolio(
            portfolio_id=portfolio_id,
            tenant_id=current_user.tenant_id,
            updates=validated_data
        )
        if not updated_portfolio:
            raise_not_found_error("Portfolio", portfolio_id)

        return PortfolioResponse.model_validate(updated_portfolio)
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to update portfolio: {str(e)}")

@investment_router.delete("/portfolios/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_feature("investments")
async def delete_portfolio(
    portfolio_id: int = Depends(validate_portfolio_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a portfolio (only if no holdings)"""
    try:
        service = PortfolioService(db)

        # Validate tenant access
        if not service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        success = service.delete_portfolio(
            portfolio_id=portfolio_id,
            tenant_id=current_user.tenant_id
        )
        if not success:
            raise_not_found_error("Portfolio", portfolio_id)

        return None
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to delete portfolio: {str(e)}")

# Holdings endpoints
@investment_router.post("/portfolios/{portfolio_id}/holdings", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
@require_feature("investments")
async def create_holding(
    holding: HoldingCreate,
    portfolio_id: int = Depends(validate_portfolio_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new holding in a portfolio"""
    try:
        # Validate portfolio access first
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        # Validate and normalize input data
        validated_data = RequestValidationMiddleware.validate_holding_create_request(holding.dict())

        holdings_service = HoldingsService(db)
        created_holding = holdings_service.create_holding(
            portfolio_id=portfolio_id,
            holding_data=validated_data
        )
        return HoldingResponse.model_validate(created_holding)
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to create holding: {str(e)}")

@investment_router.get("/portfolios/{portfolio_id}/holdings", response_model=List[HoldingResponse])
@require_feature("investments")
async def get_holdings(
    portfolio_id: int = Depends(validate_portfolio_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_closed: bool = False
):
    """Get all holdings for a portfolio"""
    try:
        # Validate portfolio access first
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        holdings_service = HoldingsService(db)
        holdings = holdings_service.get_holdings(
            portfolio_id=portfolio_id,
            include_closed=include_closed
        )
        return [HoldingResponse.model_validate(h) for h in holdings]
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to retrieve holdings: {str(e)}")

@investment_router.get("/holdings/{holding_id}", response_model=HoldingResponse)
@require_feature("investments")
async def get_holding(
    holding_id: int = Depends(validate_holding_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific holding"""
    try:
        holdings_service = HoldingsService(db)
        holding = holdings_service.get_holding(holding_id)
        if not holding:
            raise_not_found_error("Holding", holding_id)

        # Validate tenant access through portfolio
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(holding.portfolio_id, current_user.tenant_id):
            raise_tenant_access_error("Holding", holding_id)

        return HoldingResponse.model_validate(holding)
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to retrieve holding: {str(e)}")

@investment_router.put("/holdings/{holding_id}", response_model=HoldingResponse)
@require_feature("investments")
async def update_holding(
    holding: HoldingUpdate,
    holding_id: int = Depends(validate_holding_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a holding"""
    try:
        # Validate and normalize input data
        validated_data = RequestValidationMiddleware.validate_holding_update_request(
            holding.dict(exclude_unset=True)
        )

        holdings_service = HoldingsService(db)

        # Get existing holding to validate tenant access
        existing_holding = holdings_service.get_holding(holding_id)
        if not existing_holding:
            raise_not_found_error("Holding", holding_id)

        # Validate tenant access through portfolio
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(existing_holding.portfolio_id, current_user.tenant_id):
            raise_tenant_access_error("Holding", holding_id)

        updated_holding = holdings_service.update_holding(
            holding_id=holding_id,
            updates=validated_data
        )
        if not updated_holding:
            raise_not_found_error("Holding", holding_id)

        return HoldingResponse.model_validate(updated_holding)
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to update holding: {str(e)}")

@investment_router.patch("/holdings/{holding_id}/price", response_model=HoldingResponse)
@require_feature("investments")
async def update_holding_price(
    price_update: PriceUpdate,
    holding_id: int = Depends(validate_holding_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the current price of a holding"""
    try:
        # Validate and normalize input data
        validated_data = RequestValidationMiddleware.validate_price_update_request(price_update.dict())

        holdings_service = HoldingsService(db)

        # Get existing holding to validate tenant access
        existing_holding = holdings_service.get_holding(holding_id)
        if not existing_holding:
            raise_not_found_error("Holding", holding_id)

        # Validate tenant access through portfolio
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(existing_holding.portfolio_id, current_user.tenant_id):
            raise_tenant_access_error("Holding", holding_id)

        updated_holding = holdings_service.update_price(
            tenant_id=current_user.tenant_id,
            holding_id=holding_id,
            price=validated_data["current_price"]
        )
        if not updated_holding:
            raise_not_found_error("Holding", holding_id)

        return HoldingResponse.model_validate(updated_holding)
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to update holding price: {str(e)}")

# Transaction endpoints
@investment_router.post("/portfolios/{portfolio_id}/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
@require_feature("investments")
async def create_transaction(
    transaction: dict,
    portfolio_id: int = Depends(validate_portfolio_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a transaction (buy, sell, dividend, interest, fee, transfer, contribution)"""
    try:
        # Validate portfolio access first
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        # Validate and normalize transaction data
        validated_data = RequestValidationMiddleware.validate_transaction_request(transaction)

        # Check for duplicate transactions
        duplicate_detector = DuplicateTransactionDetector(db)
        duplicate_detector.check_for_duplicate(portfolio_id, validated_data)

        transaction_service = TransactionService(db)
        created_transaction = transaction_service.record_transaction(
            tenant_id=current_user.tenant_id,
            portfolio_id=portfolio_id,
            transaction_data=validated_data
        )
        return created_transaction
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to create transaction: {str(e)}")

@investment_router.get("/portfolios/{portfolio_id}/transactions", response_model=List[TransactionResponse])
@require_feature("investments")
async def get_transactions(
    portfolio_id: int = Depends(validate_portfolio_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    date_range: tuple = Depends(validate_date_range_params)
):
    """Get transactions for a portfolio with optional date filtering"""
    try:
        # Validate portfolio access first
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        start_date, end_date = date_range

        transaction_service = TransactionService(db)
        transactions = transaction_service.get_transactions(
            portfolio_id=portfolio_id,
            start_date=start_date,
            end_date=end_date
        )
        return [TransactionResponse.model_validate(t) for t in transactions]
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to retrieve transactions: {str(e)}")

@investment_router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
@require_feature("investments")
async def get_transaction(
    transaction_id: int = Depends(validate_transaction_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific transaction"""
    try:
        transaction_service = TransactionService(db)
        transaction = transaction_service.get_transaction(transaction_id)
        if not transaction:
            raise_not_found_error("Transaction", transaction_id)

        # Validate tenant access through portfolio
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(transaction.portfolio_id, current_user.tenant_id):
            raise_tenant_access_error("Transaction", transaction_id)

        return TransactionResponse.model_validate(transaction)
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to retrieve transaction: {str(e)}")

# Analytics endpoints
@investment_router.get("/portfolios/{portfolio_id}/performance", response_model=PerformanceMetrics)
@require_feature("investments")
async def get_portfolio_performance(
    portfolio_id: int = Depends(validate_portfolio_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio performance metrics (inception-to-date)"""
    try:
        # Validate portfolio access first
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        analytics_service = AnalyticsService(db)
        performance = analytics_service.calculate_portfolio_performance(portfolio_id)
        return performance
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to calculate performance: {str(e)}")

@investment_router.get("/portfolios/{portfolio_id}/allocation", response_model=AssetAllocation)
@require_feature("investments")
async def get_asset_allocation(
    portfolio_id: int = Depends(validate_portfolio_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get asset allocation analysis"""
    try:
        # Validate portfolio access first
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        analytics_service = AnalyticsService(db)
        allocation = analytics_service.calculate_asset_allocation(portfolio_id)
        return allocation
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to calculate asset allocation: {str(e)}")

@investment_router.get("/portfolios/{portfolio_id}/dividends", response_model=DividendSummary)
@require_feature("investments")
async def get_dividend_summary(
    portfolio_id: int = Depends(validate_portfolio_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    date_range: tuple = Depends(validate_date_range_params)
):
    """Get dividend summary for a time period"""
    try:
        # Validate portfolio access first
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        start_date, end_date = date_range

        analytics_service = AnalyticsService(db)
        dividend_summary = analytics_service.calculate_dividend_income(
            tenant_id=current_user.tenant_id,
            portfolio_id=portfolio_id,
            start_date=start_date,
            end_date=end_date
        )
        return dividend_summary
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to calculate dividend summary: {str(e)}")

@investment_router.get("/portfolios/{portfolio_id}/dividends/yields")
@require_feature("investments")
async def get_dividend_yields(
    portfolio_id: int = Depends(validate_portfolio_id_param),
    period_months: int = Query(12, ge=1, le=60, description="Number of months to calculate yield over"),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dividend yields for all holdings in a portfolio"""
    try:
        # Validate portfolio access first
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        analytics_service = AnalyticsService(db)
        dividend_yields = analytics_service.calculate_dividend_yield_by_holding(
            tenant_id=current_user.tenant_id,
            portfolio_id=portfolio_id,
            period_months=period_months
        )

        return {
            "portfolio_id": portfolio_id,
            "period_months": period_months,
            "dividend_yields": dividend_yields
        }
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to calculate dividend yields: {str(e)}")

@investment_router.get("/portfolios/{portfolio_id}/dividends/frequency")
@require_feature("investments")
async def get_dividend_frequency_analysis(
    portfolio_id: int = Depends(validate_portfolio_id_param),
    lookback_months: int = Query(24, ge=6, le=60, description="Number of months to analyze"),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dividend payment frequency analysis for holdings"""
    try:
        # Validate portfolio access first
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        analytics_service = AnalyticsService(db)
        frequency_analysis = analytics_service.get_dividend_frequency_analysis(
            tenant_id=current_user.tenant_id,
            portfolio_id=portfolio_id,
            lookback_months=lookback_months
        )

        return {
            "portfolio_id": portfolio_id,
            "lookback_months": lookback_months,
            "frequency_analysis": frequency_analysis
        }
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to analyze dividend frequency: {str(e)}")

@investment_router.get("/portfolios/{portfolio_id}/dividends/forecast")
@require_feature("investments")
async def get_dividend_forecast(
    portfolio_id: int = Depends(validate_portfolio_id_param),
    forecast_months: int = Query(12, ge=1, le=36, description="Number of months to forecast"),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dividend income forecast based on historical patterns"""
    try:
        # Validate portfolio access first
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        analytics_service = AnalyticsService(db)
        forecast = analytics_service.forecast_dividend_income(
            tenant_id=current_user.tenant_id,
            portfolio_id=portfolio_id,
            forecast_months=forecast_months
        )

        return {
            "portfolio_id": portfolio_id,
            **forecast
        }
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to generate dividend forecast: {str(e)}")

@investment_router.get("/portfolios/{portfolio_id}/tax-export", response_model=TaxExport)
@require_feature("investments")
async def export_tax_data(
    portfolio_id: int = Depends(validate_portfolio_id_param),
    tax_year: int = Depends(validate_tax_year_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export tax data for a specific year"""
    try:
        # Validate portfolio access first
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        analytics_service = AnalyticsService(db)
        tax_export = analytics_service.export_tax_data(
            portfolio_id=portfolio_id,
            tax_year=tax_year
        )
        return tax_export
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to export tax data: {str(e)}")

# Portfolio data export endpoints (separate from tax export)
@investment_router.get("/portfolios/{portfolio_id}/export")
@require_feature("investments")
async def export_portfolio_data(
    portfolio_id: int = Depends(validate_portfolio_id_param),
    format: str = "json",
    include_performance: bool = True,
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export complete portfolio data for backup/migration purposes"""
    try:
        # Validate portfolio access first
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        analytics_service = AnalyticsService(db)
        export_data = analytics_service.export_portfolio_data(
            tenant_id=current_user.tenant_id,
            portfolio_id=portfolio_id,
            format=format,
            include_performance=include_performance
        )

        # Return appropriate content type based on format
        if format.lower() == "csv":
            from fastapi.responses import Response
            return Response(
                content=export_data,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}_export.csv"}
            )
        else:
            from fastapi.responses import Response
            return Response(
                content=export_data,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}_export.json"}
            )
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to export portfolio data: {str(e)}")

@investment_router.get("/portfolios/{portfolio_id}/export/transactions")
@require_feature("investments")
async def export_transactions_csv(
    portfolio_id: int = Depends(validate_portfolio_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export transactions to CSV format for spreadsheet analysis"""
    try:
        # Validate portfolio access first
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        analytics_service = AnalyticsService(db)
        csv_data = analytics_service.export_transactions_csv(
            tenant_id=current_user.tenant_id,
            portfolio_id=portfolio_id
        )

        from fastapi.responses import Response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}_transactions.csv"}
        )
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to export transactions: {str(e)}")

@investment_router.get("/portfolios/{portfolio_id}/export/holdings")
@require_feature("investments")
async def export_holdings_csv(
    portfolio_id: int = Depends(validate_portfolio_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export holdings to CSV format for spreadsheet analysis"""
    try:
        # Validate portfolio access first
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        analytics_service = AnalyticsService(db)
        csv_data = analytics_service.export_holdings_csv(
            tenant_id=current_user.tenant_id,
            portfolio_id=portfolio_id
        )

        from fastapi.responses import Response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}_holdings.csv"}
        )
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to export holdings: {str(e)}")

@investment_router.get("/portfolios/{portfolio_id}/backup")
@require_feature("investments")
async def get_portfolio_backup_data(
    portfolio_id: int = Depends(validate_portfolio_id_param),
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete portfolio data for backup purposes"""
    try:
        # Validate portfolio access first
        portfolio_service = PortfolioService(db)
        if not portfolio_service.validate_tenant_access(portfolio_id, current_user.tenant_id):
            raise_not_found_error("Portfolio", portfolio_id)

        analytics_service = AnalyticsService(db)
        backup_data = analytics_service.get_portfolio_backup_data(
            tenant_id=current_user.tenant_id,
            portfolio_id=portfolio_id
        )

        return backup_data
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to get portfolio backup data: {str(e)}")

# Business portfolio endpoints for portfolio type filtering
@investment_router.get("/portfolios/by-type/{portfolio_type}", response_model=List[PortfolioResponse])
@require_feature("investments")
async def get_portfolios_by_type(
    portfolio_type: PortfolioType,
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_archived: bool = False
):
    """Get portfolios filtered by type (TAXABLE, RETIREMENT, BUSINESS)"""
    try:
        service = PortfolioService(db)
        portfolios = service.get_portfolios_by_type(
            tenant_id=current_user.tenant_id,
            portfolio_type=portfolio_type,
            include_archived=include_archived
        )
        return [PortfolioResponse.model_validate(p) for p in portfolios]
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to retrieve portfolios by type: {str(e)}")

@investment_router.get("/analytics/aggregated", response_model=dict)
@require_feature("investments")
async def get_aggregated_analytics(
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    portfolio_type: Optional[PortfolioType] = None
):
    """Get aggregated analytics across portfolios, optionally filtered by type"""
    try:
        analytics_service = AnalyticsService(db)
        aggregated_data = analytics_service.get_aggregated_analytics_by_type(
            tenant_id=current_user.tenant_id,
            portfolio_type=portfolio_type
        )
        return aggregated_data
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to calculate aggregated analytics: {str(e)}")

@investment_router.get("/analytics/business-summary", response_model=dict)
@require_feature("investments")
async def get_business_analytics_summary(
    current_user: MasterUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics summary specifically for business portfolios"""
    try:
        analytics_service = AnalyticsService(db)
        business_data = analytics_service.get_aggregated_analytics_by_type(
            tenant_id=current_user.tenant_id,
            portfolio_type=PortfolioType.BUSINESS
        )
        return business_data
    except InvestmentError:
        raise
    except Exception as e:
        raise InvestmentError(f"Failed to calculate business analytics: {str(e)}")