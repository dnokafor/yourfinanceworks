"""
Base exception classes for the application.

This module defines common exception types used throughout the application
for consistent error handling and reporting.
"""


class BaseApplicationError(Exception):
    """Base class for all application-specific exceptions."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseApplicationError):
    """Raised when input validation fails."""
    pass


class NotFoundError(BaseApplicationError):
    """Raised when a requested resource is not found."""
    pass


class ForbiddenError(BaseApplicationError):
    """Raised when access to a resource is forbidden."""
    pass


class ConflictError(BaseApplicationError):
    """Raised when a request conflicts with the current state."""
    pass


class BusinessRuleError(BaseApplicationError):
    """Raised when a business rule is violated."""
    pass


class InsufficientFundsError(BaseApplicationError):
    """Raised when there are insufficient funds for a transaction."""
    pass


class DuplicateError(BaseApplicationError):
    """Raised when attempting to create a duplicate resource."""
    pass