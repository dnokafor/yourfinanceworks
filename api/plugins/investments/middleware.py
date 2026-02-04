"""
Investment Management Middleware

This module provides middleware functions for input validation, request preprocessing,
and common validation logic for the investment management plugin.
"""

import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, date
from decimal import Decimal
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from .models import PortfolioType, SecurityType, AssetClass, TransactionType, DividendType
from .exceptions import ValidationError, InvalidEnumValueError
from .validation import ValidationUtils, PortfolioValidator, HoldingValidator, TransactionValidator

# Set up logger
logger = logging.getLogger(__name__)

# Security scheme for API key validation (if needed)
security = HTTPBearer()


class ValidationMiddleware:
    """Middleware class for input validation"""

    @staticmethod
    def validate_portfolio_id(portfolio_id: int) -> int:
        """
        Validate portfolio ID parameter.

        Args:
            portfolio_id: Portfolio ID from path parameter

        Returns:
            Validated portfolio ID

        Raises:
            ValidationError: If portfolio ID is invalid
        """
        if not isinstance(portfolio_id, int) or portfolio_id <= 0:
            raise ValidationError(
                "Portfolio ID must be a positive integer",
                [{"field": "portfolio_id", "message": "Must be a positive integer"}]
            )
        return portfolio_id

    @staticmethod
    def validate_holding_id(holding_id: int) -> int:
        """
        Validate holding ID parameter.

        Args:
            holding_id: Holding ID from path parameter

        Returns:
            Validated holding ID

        Raises:
            ValidationError: If holding ID is invalid
        """
        if not isinstance(holding_id, int) or holding_id <= 0:
            raise ValidationError(
                "Holding ID must be a positive integer",
                [{"field": "holding_id", "message": "Must be a positive integer"}]
            )
        return holding_id

    @staticmethod
    def validate_transaction_id(transaction_id: int) -> int:
        """
        Validate transaction ID parameter.

        Args:
            transaction_id: Transaction ID from path parameter

        Returns:
            Validated transaction ID

        Raises:
            ValidationError: If transaction ID is invalid
        """
        if not isinstance(transaction_id, int) or transaction_id <= 0:
            raise ValidationError(
                "Transaction ID must be a positive integer",
                [{"field": "transaction_id", "message": "Must be a positive integer"}]
            )
        return transaction_id

    @staticmethod
    def validate_tax_year(tax_year: int) -> int:
        """
        Validate tax year parameter.

        Args:
            tax_year: Tax year from query parameter

        Returns:
            Validated tax year

        Raises:
            ValidationError: If tax year is invalid
        """
        current_year = datetime.now().year
        if not isinstance(tax_year, int) or tax_year < 1900 or tax_year > current_year:
            raise ValidationError(
                f"Tax year must be between 1900 and {current_year}",
                [{"field": "tax_year", "message": f"Must be between 1900 and {current_year}"}]
            )
        return tax_year

    @staticmethod
    def validate_date_range(start_date: Optional[date], end_date: Optional[date]) -> tuple:
        """
        Validate date range parameters.

        Args:
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            Tuple of (start_date, end_date)

        Raises:
            ValidationError: If date range is invalid
        """
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError(
                    "End date must be after start date",
                    [{"field": "end_date", "message": "Must be after start date"}]
                )

        # Validate dates are not in the future
        today = date.today()
        if start_date and start_date > today:
            raise ValidationError(
                "Start date cannot be in the future",
                [{"field": "start_date", "message": "Cannot be in the future"}]
            )

        if end_date and end_date > today:
            raise ValidationError(
                "End date cannot be in the future",
                [{"field": "end_date", "message": "Cannot be in the future"}]
            )

        return start_date, end_date

    @staticmethod
    def validate_pagination_params(limit: Optional[int] = None, offset: Optional[int] = None) -> tuple:
        """
        Validate pagination parameters.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (limit, offset)

        Raises:
            ValidationError: If pagination parameters are invalid
        """
        if limit is not None:
            if not isinstance(limit, int) or limit <= 0 or limit > 1000:
                raise ValidationError(
                    "Limit must be between 1 and 1000",
                    [{"field": "limit", "message": "Must be between 1 and 1000"}]
                )

        if offset is not None:
            if not isinstance(offset, int) or offset < 0:
                raise ValidationError(
                    "Offset must be non-negative",
                    [{"field": "offset", "message": "Must be non-negative"}]
                )

        return limit, offset


class RequestValidationMiddleware:
    """Middleware for validating request bodies"""

    @staticmethod
    def validate_portfolio_create_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate portfolio creation request.

        Args:
            request_data: Request body data

        Returns:
            Validated and normalized request data

        Raises:
            ValidationError: If validation fails
        """
        # Validate using the portfolio validator
        PortfolioValidator.validate_portfolio_create(request_data)

        # Normalize data
        normalized_data = request_data.copy()
        normalized_data["name"] = normalized_data["name"].strip()

        # Ensure portfolio_type is enum
        if isinstance(normalized_data["portfolio_type"], str):
            normalized_data["portfolio_type"] = PortfolioType(normalized_data["portfolio_type"])

        return normalized_data

    @staticmethod
    def validate_portfolio_update_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate portfolio update request.

        Args:
            request_data: Request body data

        Returns:
            Validated and normalized request data

        Raises:
            ValidationError: If validation fails
        """
        # Remove None values
        filtered_data = {k: v for k, v in request_data.items() if v is not None}

        if not filtered_data:
            raise ValidationError("At least one field must be provided for update")

        # Validate using the portfolio validator
        PortfolioValidator.validate_portfolio_update(filtered_data)

        # Normalize data
        normalized_data = filtered_data.copy()
        if "name" in normalized_data:
            normalized_data["name"] = normalized_data["name"].strip()

        # Ensure portfolio_type is enum
        if "portfolio_type" in normalized_data and isinstance(normalized_data["portfolio_type"], str):
            normalized_data["portfolio_type"] = PortfolioType(normalized_data["portfolio_type"])

        return normalized_data

    @staticmethod
    def validate_holding_create_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate holding creation request.

        Args:
            request_data: Request body data

        Returns:
            Validated and normalized request data

        Raises:
            ValidationError: If validation fails
        """
        # Validate using the holding validator
        HoldingValidator.validate_holding_create(request_data)

        # Normalize data
        normalized_data = request_data.copy()
        normalized_data["security_symbol"] = normalized_data["security_symbol"].strip().upper()

        if "security_name" in normalized_data and normalized_data["security_name"]:
            normalized_data["security_name"] = normalized_data["security_name"].strip()

        # Ensure enums are proper enum types
        if isinstance(normalized_data["security_type"], str):
            normalized_data["security_type"] = SecurityType(normalized_data["security_type"])

        if isinstance(normalized_data["asset_class"], str):
            normalized_data["asset_class"] = AssetClass(normalized_data["asset_class"])

        # Ensure numeric fields are Decimal
        normalized_data["quantity"] = Decimal(str(normalized_data["quantity"]))
        normalized_data["cost_basis"] = Decimal(str(normalized_data["cost_basis"]))

        # Ensure purchase_date is date object
        if isinstance(normalized_data["purchase_date"], str):
            normalized_data["purchase_date"] = datetime.fromisoformat(normalized_data["purchase_date"]).date()

        return normalized_data

    @staticmethod
    def validate_holding_update_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate holding update request.

        Args:
            request_data: Request body data

        Returns:
            Validated and normalized request data

        Raises:
            ValidationError: If validation fails
        """
        # Remove None values
        filtered_data = {k: v for k, v in request_data.items() if v is not None}

        if not filtered_data:
            raise ValidationError("At least one field must be provided for update")

        # Validate using the holding validator
        HoldingValidator.validate_holding_update(filtered_data)

        # Normalize data
        normalized_data = filtered_data.copy()

        if "security_name" in normalized_data and normalized_data["security_name"]:
            normalized_data["security_name"] = normalized_data["security_name"].strip()

        # Ensure enums are proper enum types
        if "security_type" in normalized_data and isinstance(normalized_data["security_type"], str):
            normalized_data["security_type"] = SecurityType(normalized_data["security_type"])

        if "asset_class" in normalized_data and isinstance(normalized_data["asset_class"], str):
            normalized_data["asset_class"] = AssetClass(normalized_data["asset_class"])

        # Ensure numeric fields are Decimal
        if "quantity" in normalized_data:
            normalized_data["quantity"] = Decimal(str(normalized_data["quantity"]))

        if "cost_basis" in normalized_data:
            normalized_data["cost_basis"] = Decimal(str(normalized_data["cost_basis"]))

        return normalized_data

    @staticmethod
    def validate_price_update_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate price update request.

        Args:
            request_data: Request body data

        Returns:
            Validated and normalized request data

        Raises:
            ValidationError: If validation fails
        """
        # Validate using the holding validator
        HoldingValidator.validate_price_update(request_data)

        # Normalize data
        normalized_data = request_data.copy()
        normalized_data["current_price"] = Decimal(str(normalized_data["current_price"]))

        return normalized_data

    @staticmethod
    def validate_transaction_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate transaction request.

        Args:
            request_data: Request body data

        Returns:
            Validated and normalized request data

        Raises:
            ValidationError: If validation fails
        """
        # Validate based on transaction type
        transaction_type = request_data.get("transaction_type")

        if not transaction_type:
            raise ValidationError("Transaction type is required")

        # Normalize transaction type
        if isinstance(transaction_type, str):
            try:
                transaction_type = TransactionType(transaction_type.lower())
                request_data["transaction_type"] = transaction_type
            except ValueError:
                valid_types = [t.value for t in TransactionType]
                raise InvalidEnumValueError(
                    f"Invalid transaction type. Must be one of: {', '.join(valid_types)}"
                )

        # Validate based on specific transaction type
        if transaction_type == TransactionType.BUY:
            TransactionValidator.validate_buy_transaction(request_data)
        elif transaction_type == TransactionType.SELL:
            TransactionValidator.validate_sell_transaction(request_data)
        elif transaction_type == TransactionType.DIVIDEND:
            TransactionValidator.validate_dividend_transaction(request_data)
        else:
            TransactionValidator.validate_other_transaction(request_data)

        # Normalize data
        normalized_data = request_data.copy()

        # Ensure numeric fields are Decimal
        normalized_data["total_amount"] = Decimal(str(normalized_data["total_amount"]))

        if "fees" in normalized_data and normalized_data["fees"] is not None:
            normalized_data["fees"] = Decimal(str(normalized_data["fees"]))

        if "quantity" in normalized_data and normalized_data["quantity"] is not None:
            normalized_data["quantity"] = Decimal(str(normalized_data["quantity"]))

        if "price_per_share" in normalized_data and normalized_data["price_per_share"] is not None:
            normalized_data["price_per_share"] = Decimal(str(normalized_data["price_per_share"]))

        # Ensure date fields are date objects
        if isinstance(normalized_data["transaction_date"], str):
            normalized_data["transaction_date"] = datetime.fromisoformat(normalized_data["transaction_date"]).date()

        if "payment_date" in normalized_data and normalized_data["payment_date"]:
            if isinstance(normalized_data["payment_date"], str):
                normalized_data["payment_date"] = datetime.fromisoformat(normalized_data["payment_date"]).date()

        if "ex_dividend_date" in normalized_data and normalized_data["ex_dividend_date"]:
            if isinstance(normalized_data["ex_dividend_date"], str):
                normalized_data["ex_dividend_date"] = datetime.fromisoformat(normalized_data["ex_dividend_date"]).date()

        # Ensure dividend_type is enum
        if "dividend_type" in normalized_data and isinstance(normalized_data["dividend_type"], str):
            normalized_data["dividend_type"] = DividendType(normalized_data["dividend_type"])

        # Trim notes if provided
        if "notes" in normalized_data and normalized_data["notes"]:
            normalized_data["notes"] = normalized_data["notes"].strip()

        return normalized_data


# Dependency functions for FastAPI
def validate_portfolio_id_param(portfolio_id: int) -> int:
    """FastAPI dependency for validating portfolio ID parameter"""
    return ValidationMiddleware.validate_portfolio_id(portfolio_id)


def validate_holding_id_param(holding_id: int) -> int:
    """FastAPI dependency for validating holding ID parameter"""
    return ValidationMiddleware.validate_holding_id(holding_id)


def validate_transaction_id_param(transaction_id: int) -> int:
    """FastAPI dependency for validating transaction ID parameter"""
    return ValidationMiddleware.validate_transaction_id(transaction_id)


def validate_tax_year_param(tax_year: int) -> int:
    """FastAPI dependency for validating tax year parameter"""
    return ValidationMiddleware.validate_tax_year(tax_year)


def validate_date_range_params(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> tuple:
    """FastAPI dependency for validating date range parameters"""
    return ValidationMiddleware.validate_date_range(start_date, end_date)


def validate_pagination_params(
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> tuple:
    """FastAPI dependency for validating pagination parameters"""
    return ValidationMiddleware.validate_pagination_params(limit, offset)


# Request logging middleware
async def log_request_middleware(request: Request, call_next):
    """
    Middleware to log investment API requests for debugging and monitoring.

    Args:
        request: FastAPI request object
        call_next: Next middleware/endpoint in chain

    Returns:
        Response from the next middleware/endpoint
    """
    # Only log investment API requests
    if not request.url.path.startswith("/api/v1/investments"):
        return await call_next(request)

    start_time = datetime.utcnow()

    # Log request details
    logger.info(f"Investment API Request: {request.method} {request.url.path}")

    try:
        response = await call_next(request)

        # Log response details
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Investment API Response: {response.status_code} in {duration:.3f}s")

        return response

    except Exception as e:
        # Log error details
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"Investment API Error: {str(e)} after {duration:.3f}s")
        raise