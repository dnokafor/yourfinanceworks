"""
Feature Gate Decorator and Utilities

This module provides decorators and helper functions for gating API endpoints
and code execution behind license checks.
"""

from functools import wraps
from typing import Optional
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from models.database import get_db, get_tenant_context
from services.license_service import LicenseService


def require_feature(feature_id: str, error_message: Optional[str] = None):
    """
    Decorator to gate API endpoints behind feature license checks.
    
    Returns HTTP 402 (Payment Required) when feature is not licensed.
    
    Usage:
        @router.post("/ai/chat")
        @require_feature("ai_chat")
        async def chat_endpoint(...):
            pass
    
    Args:
        feature_id: Feature ID to check (e.g., "ai_invoice", "tax_integration")
        error_message: Optional custom error message
        
    Returns:
        Decorator function that checks feature availability
        
    Raises:
        HTTPException: 402 Payment Required if feature is not licensed
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract db session from kwargs or create new one
            db: Optional[Session] = kwargs.get('db')
            close_db = False
            
            if db is None:
                # Try to get db from args (if it's a dependency)
                for arg in args:
                    if isinstance(arg, Session):
                        db = arg
                        break
            
            if db is None:
                # Create a new session
                db = next(get_db())
                close_db = True
            
            try:
                # Check if feature is enabled
                license_service = LicenseService(db)
                
                if not license_service.has_feature(feature_id):
                    # Get trial status for better error message
                    trial_status = license_service.get_trial_status()
                    license_status = license_service.get_license_status()
                    
                    # Determine appropriate message
                    if trial_status["is_trial"] and not trial_status["trial_active"]:
                        if trial_status["in_grace_period"]:
                            message = (
                                f"Your trial has expired. You are in a {trial_status['grace_period_end'].strftime('%d')} grace period. "
                                f"Please activate a license to continue using the '{feature_id}' feature."
                            )
                        else:
                            message = (
                                f"Your trial has expired. Please activate a license to use the '{feature_id}' feature."
                            )
                    elif license_status["is_licensed"]:
                        message = (
                            f"The '{feature_id}' feature is not included in your current license. "
                            f"Please upgrade your license to access this feature."
                        )
                    else:
                        message = (
                            f"The '{feature_id}' feature requires a valid license. "
                            f"Please activate a license or start a trial."
                        )
                    
                    # Use custom message if provided
                    if error_message:
                        message = error_message
                    
                    # Check if feature is enabled via config service (fallback to env/default)
                    # This handles the case where license status is "invalid" (fresh install)
                    from services.feature_config_service import FeatureConfigService
                    if FeatureConfigService.is_enabled(feature_id, db, check_license=False):
                        # Feature enabled via config/env, allow access
                        return await func(*args, **kwargs)

                    raise HTTPException(
                        status_code=402,
                        detail={
                            "error": "FEATURE_NOT_LICENSED",
                            "message": message,
                            "feature_id": feature_id,
                            "license_status": license_status["license_status"],
                            "trial_active": trial_status["trial_active"],
                            "in_grace_period": trial_status["in_grace_period"],
                            "upgrade_required": True
                        }
                    )
                
                # Feature is enabled, execute the function
                return await func(*args, **kwargs)
                
            finally:
                if close_db:
                    db.close()
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract db session from kwargs or create new one
            db: Optional[Session] = kwargs.get('db')
            close_db = False
            
            if db is None:
                # Try to get db from args (if it's a dependency)
                for arg in args:
                    if isinstance(arg, Session):
                        db = arg
                        break
            
            if db is None:
                # Create a new session
                db = next(get_db())
                close_db = True
            
            try:
                # Check if feature is enabled
                license_service = LicenseService(db)
                
                if not license_service.has_feature(feature_id):
                    # Get trial status for better error message
                    trial_status = license_service.get_trial_status()
                    license_status = license_service.get_license_status()
                    
                    # Determine appropriate message
                    if trial_status["is_trial"] and not trial_status["trial_active"]:
                        if trial_status["in_grace_period"]:
                            message = (
                                f"Your trial has expired. You are in a grace period. "
                                f"Please activate a license to continue using the '{feature_id}' feature."
                            )
                        else:
                            message = (
                                f"Your trial has expired. Please activate a license to use the '{feature_id}' feature."
                            )
                    elif license_status["is_licensed"]:
                        message = (
                            f"The '{feature_id}' feature is not included in your current license. "
                            f"Please upgrade your license to access this feature."
                        )
                    else:
                        message = (
                            f"The '{feature_id}' feature requires a valid license. "
                            f"Please activate a license or start a trial."
                        )
                    
                    # Use custom message if provided
                    if error_message:
                        message = error_message
                    
                    # Check if feature is enabled via config service (fallback to env/default)
                    # This handles the case where license status is "invalid" (fresh install)
                    from services.feature_config_service import FeatureConfigService
                    if FeatureConfigService.is_enabled(feature_id, db, check_license=False):
                        # Feature enabled via config/env, allow access
                        return func(*args, **kwargs)

                    raise HTTPException(
                        status_code=402,
                        detail={
                            "error": "FEATURE_NOT_LICENSED",
                            "message": message,
                            "feature_id": feature_id,
                            "license_status": license_status["license_status"],
                            "trial_active": trial_status["trial_active"],
                            "in_grace_period": trial_status["in_grace_period"],
                            "upgrade_required": True
                        }
                    )
                
                # Feature is enabled, execute the function
                return func(*args, **kwargs)
                
            finally:
                if close_db:
                    db.close()
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def feature_enabled(feature_id: str, db: Optional[Session] = None) -> bool:
    """
    Helper function to check feature status in code.
    
    This is useful for conditional execution within endpoints or services.
    
    Usage:
        if feature_enabled("ai_invoice", db):
            # Execute AI processing
        else:
            # Use fallback method
    
    Args:
        feature_id: Feature ID to check (e.g., "ai_invoice", "tax_integration")
        db: Database session (optional, will create new one if not provided)
        
    Returns:
        True if feature is enabled, False otherwise
    """
    close_db = False
    
    if db is None:
        db = next(get_db())
        close_db = True
    
    try:
        license_service = LicenseService(db)
        return license_service.has_feature(feature_id)
    finally:
        if close_db:
            db.close()


def get_enabled_features(db: Optional[Session] = None) -> list:
    """
    Get list of all enabled features.
    
    Args:
        db: Database session (optional, will create new one if not provided)
        
    Returns:
        List of enabled feature IDs
    """
    close_db = False
    
    if db is None:
        db = next(get_db())
        close_db = True
    
    try:
        license_service = LicenseService(db)
        return license_service.get_enabled_features()
    finally:
        if close_db:
            db.close()


def require_business_license(func):
    """
    Decorator to gate API endpoints behind business license requirement.
    
    This decorator ensures that only users with a business license (trial or paid)
    can access the endpoint. Personal use licenses will be denied.
    
    Returns HTTP 403 (Forbidden) when user has personal license.
    
    Usage:
        @router.post("/external-auth/api-keys")
        @require_business_license
        async def create_api_key(...):
            pass
    
    Returns:
        Decorator function that checks business license requirement
        
    Raises:
        HTTPException: 403 Forbidden if user has personal license only
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Get tenant database session (installation_info is in tenant DB)
        # get_db() returns tenant database in authenticated context
        tenant_db = next(get_db())
        close_db = True
        
        try:
            # Check license status using tenant database
            license_service = LicenseService(tenant_db)
            license_status = license_service.get_license_status()
            
            # Personal use licenses are not allowed
            if license_status.get("is_personal"):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "BUSINESS_LICENSE_REQUIRED",
                        "message": (
                            "This feature requires a business license. "
                            "Personal use licenses do not include access to API keys and external integrations. "
                            "Please upgrade to a business license to access this feature."
                        ),
                        "license_status": "personal",
                        "upgrade_required": True,
                        "upgrade_url": "/settings?tab=license"
                    }
                )
            
            # Invalid/no license - require selection or activation
            if license_status.get("license_status") == "invalid":
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "LICENSE_REQUIRED",
                        "message": (
                            "This feature requires a business license. "
                            "Please select business use and start a trial, or activate a license."
                        ),
                        "license_status": "invalid",
                        "upgrade_required": True,
                        "upgrade_url": "/settings?tab=license"
                    }
                )
            
            # Trial expired
            if license_status.get("license_status") == "trial" and not license_status.get("trial_info", {}).get("trial_active"):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "TRIAL_EXPIRED",
                        "message": (
                            "Your trial has expired. Please activate a business license to continue using this feature."
                        ),
                        "license_status": "trial_expired",
                        "upgrade_required": True,
                        "upgrade_url": "/settings?tab=license"
                    }
                )
            
            # License expired
            if license_status.get("license_status") == "expired":
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "LICENSE_EXPIRED",
                        "message": (
                            "Your license has expired. Please renew your license to continue using this feature."
                        ),
                        "license_status": "expired",
                        "upgrade_required": True,
                        "upgrade_url": "/settings?tab=license"
                    }
                )
            
            # Business license is valid (trial or active), execute the function
            return await func(*args, **kwargs)
            
        finally:
            if close_db and tenant_db:
                tenant_db.close()
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        # Get tenant database session (installation_info is in tenant DB)
        # get_db() returns tenant database in authenticated context
        tenant_db = next(get_db())
        close_db = True
        
        try:
            # Check license status using tenant database
            license_service = LicenseService(tenant_db)
            license_status = license_service.get_license_status()
            
            # Personal use licenses are not allowed
            if license_status.get("is_personal"):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "BUSINESS_LICENSE_REQUIRED",
                        "message": (
                            "This feature requires a business license. "
                            "Personal use licenses do not include access to API keys and external integrations. "
                            "Please upgrade to a business license to access this feature."
                        ),
                        "license_status": "personal",
                        "upgrade_required": True,
                        "upgrade_url": "/settings?tab=license"
                    }
                )
            
            # Invalid/no license - require selection or activation
            if license_status.get("license_status") == "invalid":
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "LICENSE_REQUIRED",
                        "message": (
                            "This feature requires a business license. "
                            "Please select business use and start a trial, or activate a license."
                        ),
                        "license_status": "invalid",
                        "upgrade_required": True,
                        "upgrade_url": "/settings?tab=license"
                    }
                )
            
            # Trial expired
            if license_status.get("license_status") == "trial" and not license_status.get("trial_info", {}).get("trial_active"):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "TRIAL_EXPIRED",
                        "message": (
                            "Your trial has expired. Please activate a business license to continue using this feature."
                        ),
                        "license_status": "trial_expired",
                        "upgrade_required": True,
                        "upgrade_url": "/settings?tab=license"
                    }
                )
            
            # License expired
            if license_status.get("license_status") == "expired":
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "LICENSE_EXPIRED",
                        "message": (
                            "Your license has expired. Please renew your license to continue using this feature."
                        ),
                        "license_status": "expired",
                        "upgrade_required": True,
                        "upgrade_url": "/settings?tab=license"
                    }
                )
            
            # Business license is valid (trial or active), execute the function
            return func(*args, **kwargs)
            
        finally:
            if close_db and tenant_db:
                tenant_db.close()
    
    # Return appropriate wrapper based on function type
    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
