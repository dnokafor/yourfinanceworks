"""
Encryption Exception Classes for tenant database encryption.

This module provides custom exception classes for encryption-related errors
with comprehensive error handling and retry logic capabilities.
"""

import logging
import time
from typing import Optional, Dict, Any, Callable, Type
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)


class EncryptionErrorCode(Enum):
    """Error codes for encryption operations."""
    GENERAL_ERROR = "ENC_001"
    KEY_NOT_FOUND = "ENC_002"
    DECRYPTION_FAILED = "ENC_003"
    KEY_ROTATION_FAILED = "ENC_004"
    INVALID_DATA = "ENC_005"
    CONFIGURATION_ERROR = "ENC_006"
    KEY_GENERATION_FAILED = "ENC_007"
    MASTER_KEY_ERROR = "ENC_008"
    VAULT_CONNECTION_ERROR = "ENC_009"
    PERMISSION_DENIED = "ENC_010"
    TRANSIENT_ERROR = "ENC_011"


class EncryptionError(Exception):
    """
    Base exception class for encryption-related errors.
    
    Provides structured error information and logging capabilities
    without exposing sensitive data.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: EncryptionErrorCode = EncryptionErrorCode.GENERAL_ERROR,
        tenant_id: Optional[int] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        Initialize encryption error.
        
        Args:
            message: Human-readable error message
            error_code: Specific error code for categorization
            tenant_id: Tenant ID associated with the error (if applicable)
            operation: Operation that failed
            details: Additional non-sensitive error details
            original_exception: Original exception that caused this error
        """
        super().__init__(message)
        self.error_code = error_code
        self.tenant_id = tenant_id
        self.operation = operation
        self.details = details or {}
        self.original_exception = original_exception
        self.timestamp = time.time()
        
        # Log error without sensitive information
        self._log_error()
    
    def _log_error(self):
        """Log error information without exposing sensitive data."""
        log_data = {
            "error_code": self.error_code.value,
            "message": str(self),
            "tenant_id": self.tenant_id,
            "operation": self.operation,
            "timestamp": self.timestamp,
            "details": self._sanitize_details(self.details)
        }
        
        if self.original_exception:
            log_data["original_error_type"] = type(self.original_exception).__name__
        
        logger.error(f"Encryption error: {log_data}")
    
    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize error details to remove sensitive information.
        
        Args:
            details: Original error details
            
        Returns:
            Sanitized details dictionary
        """
        sanitized = {}
        sensitive_keys = {'key', 'password', 'token', 'secret', 'credential'}
        
        for key, value in details.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary representation.
        
        Returns:
            Dictionary with error information
        """
        return {
            "error_code": self.error_code.value,
            "message": str(self),
            "tenant_id": self.tenant_id,
            "operation": self.operation,
            "timestamp": self.timestamp,
            "details": self._sanitize_details(self.details)
        }
    
    def is_retryable(self) -> bool:
        """
        Check if this error is retryable.
        
        Returns:
            True if the operation can be retried
        """
        retryable_codes = {
            EncryptionErrorCode.TRANSIENT_ERROR,
            EncryptionErrorCode.VAULT_CONNECTION_ERROR
        }
        return self.error_code in retryable_codes


class KeyNotFoundError(EncryptionError):
    """Exception raised when an encryption key cannot be found."""
    
    def __init__(
        self, 
        message: str = "Encryption key not found",
        tenant_id: Optional[int] = None,
        key_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if key_id:
            details['key_id'] = key_id
        
        super().__init__(
            message=message,
            error_code=EncryptionErrorCode.KEY_NOT_FOUND,
            tenant_id=tenant_id,
            operation="key_retrieval",
            details=details,
            **{k: v for k, v in kwargs.items() if k != 'details'}
        )


class DecryptionError(EncryptionError):
    """Exception raised when data decryption fails."""
    
    def __init__(
        self, 
        message: str = "Data decryption failed",
        tenant_id: Optional[int] = None,
        data_type: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if data_type:
            details['data_type'] = data_type
        
        super().__init__(
            message=message,
            error_code=EncryptionErrorCode.DECRYPTION_FAILED,
            tenant_id=tenant_id,
            operation="decryption",
            details=details,
            **{k: v for k, v in kwargs.items() if k != 'details'}
        )


class KeyRotationError(EncryptionError):
    """Exception raised when key rotation fails."""
    
    def __init__(
        self, 
        message: str = "Key rotation failed",
        tenant_id: Optional[int] = None,
        rotation_phase: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if rotation_phase:
            details['rotation_phase'] = rotation_phase
        
        super().__init__(
            message=message,
            error_code=EncryptionErrorCode.KEY_ROTATION_FAILED,
            tenant_id=tenant_id,
            operation="key_rotation",
            details=details,
            **{k: v for k, v in kwargs.items() if k != 'details'}
        )


class InvalidDataError(EncryptionError):
    """Exception raised when data is invalid for encryption/decryption."""
    
    def __init__(
        self, 
        message: str = "Invalid data for encryption operation",
        tenant_id: Optional[int] = None,
        validation_error: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if validation_error:
            details['validation_error'] = validation_error
        
        super().__init__(
            message=message,
            error_code=EncryptionErrorCode.INVALID_DATA,
            tenant_id=tenant_id,
            operation="data_validation",
            details=details,
            **{k: v for k, v in kwargs.items() if k != 'details'}
        )


class ConfigurationError(EncryptionError):
    """Exception raised when encryption configuration is invalid."""
    
    def __init__(
        self, 
        message: str = "Encryption configuration error",
        config_field: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if config_field:
            details['config_field'] = config_field
        
        super().__init__(
            message=message,
            error_code=EncryptionErrorCode.CONFIGURATION_ERROR,
            operation="configuration_validation",
            details=details,
            **{k: v for k, v in kwargs.items() if k != 'details'}
        )


class KeyGenerationError(EncryptionError):
    """Exception raised when key generation fails."""
    
    def __init__(
        self, 
        message: str = "Key generation failed",
        tenant_id: Optional[int] = None,
        key_type: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if key_type:
            details['key_type'] = key_type
        
        super().__init__(
            message=message,
            error_code=EncryptionErrorCode.KEY_GENERATION_FAILED,
            tenant_id=tenant_id,
            operation="key_generation",
            details=details,
            **{k: v for k, v in kwargs.items() if k != 'details'}
        )


class MasterKeyError(EncryptionError):
    """Exception raised when master key operations fail."""
    
    def __init__(
        self, 
        message: str = "Master key operation failed",
        master_key_operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if master_key_operation:
            details['master_key_operation'] = master_key_operation
        
        super().__init__(
            message=message,
            error_code=EncryptionErrorCode.MASTER_KEY_ERROR,
            operation="master_key_operation",
            details=details,
            **{k: v for k, v in kwargs.items() if k != 'details'}
        )


class VaultConnectionError(EncryptionError):
    """Exception raised when key vault connection fails."""
    
    def __init__(
        self, 
        message: str = "Key vault connection failed",
        vault_provider: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if vault_provider:
            details['vault_provider'] = vault_provider
        
        super().__init__(
            message=message,
            error_code=EncryptionErrorCode.VAULT_CONNECTION_ERROR,
            operation="vault_connection",
            details=details,
            **{k: v for k, v in kwargs.items() if k != 'details'}
        )
    
    def is_retryable(self) -> bool:
        """Vault connection errors are retryable."""
        return True


class PermissionDeniedError(EncryptionError):
    """Exception raised when access to encryption resources is denied."""
    
    def __init__(
        self, 
        message: str = "Permission denied for encryption operation",
        tenant_id: Optional[int] = None,
        resource: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if resource:
            details['resource'] = resource
        
        super().__init__(
            message=message,
            error_code=EncryptionErrorCode.PERMISSION_DENIED,
            tenant_id=tenant_id,
            operation="permission_check",
            details=details,
            **{k: v for k, v in kwargs.items() if k != 'details'}
        )


class TransientError(EncryptionError):
    """Exception raised for temporary/transient encryption errors."""
    
    def __init__(
        self, 
        message: str = "Transient encryption error",
        tenant_id: Optional[int] = None,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if retry_after:
            details['retry_after_seconds'] = retry_after
        
        super().__init__(
            message=message,
            error_code=EncryptionErrorCode.TRANSIENT_ERROR,
            tenant_id=tenant_id,
            operation="transient_operation",
            details=details,
            **{k: v for k, v in kwargs.items() if k != 'details'}
        )
    
    def is_retryable(self) -> bool:
        """Transient errors are retryable."""
        return True


def with_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = (TransientError, VaultConnectionError)
):
    """
    Decorator for adding retry logic to encryption operations.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each attempt
        retryable_exceptions: Tuple of exception types that should trigger retry
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if exception is retryable
                    if not isinstance(e, retryable_exceptions):
                        if hasattr(e, 'is_retryable') and not e.is_retryable():
                            raise
                        elif not isinstance(e, EncryptionError):
                            raise
                    
                    # Don't retry on last attempt
                    if attempt == max_attempts - 1:
                        break
                    
                    # Log retry attempt
                    logger.warning(
                        f"Encryption operation failed (attempt {attempt + 1}/{max_attempts}), "
                        f"retrying in {current_delay}s: {str(e)}"
                    )
                    
                    # Wait before retry
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            
            # All attempts failed, raise the last exception
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def handle_encryption_error(
    operation: str,
    tenant_id: Optional[int] = None,
    reraise_as: Optional[Type[EncryptionError]] = None
):
    """
    Context manager for handling encryption errors with consistent logging.
    
    Args:
        operation: Name of the operation being performed
        tenant_id: Tenant ID associated with the operation
        reraise_as: Exception class to reraise as (if different from original)
    
    Usage:
        with handle_encryption_error("data_encryption", tenant_id=123):
            # encryption operation
            pass
    """
    class ErrorHandler:
        def __init__(self, op: str, tid: Optional[int], reraise: Optional[Type[EncryptionError]]):
            self.operation = op
            self.tenant_id = tid
            self.reraise_as = reraise
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                return False
            
            # If it's already an EncryptionError, let it propagate
            if isinstance(exc_val, EncryptionError):
                return False
            
            # Convert to EncryptionError
            error_class = self.reraise_as or EncryptionError
            
            new_error = error_class(
                message=f"Operation '{self.operation}' failed: {str(exc_val)}",
                tenant_id=self.tenant_id,
                operation=self.operation,
                original_exception=exc_val
            )
            
            raise new_error from exc_val
    
    return ErrorHandler(operation, tenant_id, reraise_as)


def log_encryption_event(
    event_type: str,
    tenant_id: Optional[int] = None,
    operation: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    level: str = "info"
):
    """
    Log encryption-related events with consistent formatting.
    
    Args:
        event_type: Type of event (success, failure, warning, etc.)
        tenant_id: Tenant ID associated with the event
        operation: Operation being performed
        details: Additional event details (will be sanitized)
        level: Log level (debug, info, warning, error)
    """
    log_data = {
        "event_type": event_type,
        "tenant_id": tenant_id,
        "operation": operation,
        "timestamp": time.time(),
        "details": _sanitize_log_details(details or {})
    }
    
    log_message = f"Encryption event: {log_data}"
    
    if level == "debug":
        logger.debug(log_message)
    elif level == "info":
        logger.info(log_message)
    elif level == "warning":
        logger.warning(log_message)
    elif level == "error":
        logger.error(log_message)
    else:
        logger.info(log_message)


def _sanitize_log_details(details: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize log details to remove sensitive information."""
    sanitized = {}
    sensitive_keys = {'key', 'password', 'token', 'secret', 'credential'}
    
    for key, value in details.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_log_details(value)
        else:
            sanitized[key] = value
    
    return sanitized