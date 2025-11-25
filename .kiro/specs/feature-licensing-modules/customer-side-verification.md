# Customer-Side License Verification Code

## Overview

This code goes into the customer's self-hosted installation. It verifies license keys using the public key (embedded in the app) without needing to contact your servers.

## Complete Implementation

### 1. Database Models

```python
# api/models/models_per_tenant.py (or models.py for global)

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class InstallationInfo(Base):
    """
    Stores installation and license information.
    One record per installation.
    """
    __tablename__ = 'installation_info'
    
    id = Column(Integer, primary_key=True)
    installation_id = Column(String(100), unique=True, nullable=False)
    
    # Trial tracking
    first_started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    trial_started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    trial_ends_at = Column(DateTime, nullable=False)
    
    # License info
    license_key = Column(Text, nullable=True)
    license_activated_at = Column(DateTime, nullable=True)
    license_expires_at = Column(DateTime, nullable=True)
    license_features = Column(JSON, nullable=True)  # Cached features list
    license_customer_email = Column(String(255), nullable=True)
    license_customer_name = Column(String(255), nullable=True)
    license_max_users = Column(Integer, nullable=True)
    
    # Validation cache
    last_validation_at = Column(DateTime, nullable=True)
    last_validation_result = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LicenseValidationLog(Base):
    """
    Audit log of license validation attempts.
    """
    __tablename__ = 'license_validation_log'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    license_key_preview = Column(String(50))  # First 50 chars for debugging
    validation_result = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
```


### 2. License Verification Service

```python
# api/services/license_service.py

import jwt
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from functools import lru_cache

from models.models_per_tenant import InstallationInfo, LicenseValidationLog

logger = logging.getLogger(__name__)

class LicenseService:
    """
    Verify and manage licenses in customer's installation.
    This code runs on the customer's server.
    """
    
    # Your public key (embedded in the application)
    # This is safe to be public - it can only VERIFY signatures, not create them
    PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAyourpublickeyhere
... (rest of your public key) ...
-----END PUBLIC KEY-----"""
    
    # Trial configuration
    TRIAL_DAYS = 30
    GRACE_PERIOD_DAYS = 7
    
    # Cache validation results for 1 hour
    VALIDATION_CACHE_SECONDS = 3600
    
    def __init__(self, db: Session):
        self.db = db
    
    def verify_license(self, license_key: str, skip_cache: bool = False) -> Dict:
        """
        Verify a license key's signature and validity.
        
        Args:
            license_key: The JWT license key to verify
            skip_cache: Force fresh validation (ignore cache)
        
        Returns:
            Dictionary with validation results:
            {
                'valid': bool,
                'customer_email': str,
                'customer_name': str,
                'features': list,
                'expires_at': datetime,
                'max_users': int,
                'days_remaining': int,
                'error': str (if invalid)
            }
        """
        try:
            # Check cache first (unless skipped)
            if not skip_cache:
                cached = self._get_cached_validation(license_key)
                if cached:
                    logger.debug("Using cached license validation")
                    return cached
            
            # Decode and verify JWT signature
            try:
                payload = jwt.decode(
                    license_key,
                    self.PUBLIC_KEY,
                    algorithms=['RS256'],
                    options={
                        'verify_signature': True,
                        'verify_exp': False,  # We'll check expiration manually
                        'verify_iat': True,
                        'verify_iss': True,
                        'require': ['iss', 'sub', 'exp', 'features']
                    }
                )
            except jwt.InvalidSignatureError:
                return self._validation_error('INVALID_SIGNATURE', 'License signature is invalid')
            except jwt.ExpiredSignatureError:
                return self._validation_error('EXPIRED', 'License has expired')
            except jwt.DecodeError as e:
                return self._validation_error('INVALID_FORMAT', f'License format is invalid: {str(e)}')
            except Exception as e:
                return self._validation_error('VERIFICATION_FAILED', f'License verification failed: {str(e)}')
            
            # Extract license data
            expires_at = datetime.fromtimestamp(payload['exp'])
            now = datetime.utcnow()
            days_remaining = (expires_at - now).days
            
            # Check if expired
            if expires_at < now:
                return self._validation_error(
                    'EXPIRED',
                    f'License expired on {expires_at.strftime("%Y-%m-%d")}',
                    extra_data={
                        'expires_at': expires_at,
                        'days_remaining': days_remaining
                    }
                )
            
            # Build successful result
            result = {
                'valid': True,
                'customer_email': payload.get('customer_email', payload.get('sub')),
                'customer_name': payload.get('customer_name', 'Licensed User'),
                'features': payload.get('features', []),
                'expires_at': expires_at,
                'max_users': payload.get('max_users'),
                'days_remaining': days_remaining,
                'license_id': payload.get('jti'),
                'license_type': payload.get('license_type', 'commercial'),
                'issued_at': datetime.fromtimestamp(payload.get('iat', 0)),
            }
            
            # Cache the result
            self._cache_validation(license_key, result)
            
            # Log successful validation
            self._log_validation(license_key, True, None)
            
            logger.info(f"License verified successfully for {result['customer_email']}, expires in {days_remaining} days")
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error during license verification: {e}")
            return self._validation_error('UNKNOWN_ERROR', str(e))
    
    def _validation_error(self, error_code: str, message: str, extra_data: dict = None) -> Dict:
        """Create a validation error response"""
        result = {
            'valid': False,
            'error': error_code,
            'message': message
        }
        if extra_data:
            result.update(extra_data)
        
        # Log failed validation
        self._log_validation(None, False, message)
        
        return result
    
    def _get_cached_validation(self, license_key: str) -> Optional[Dict]:
        """Get cached validation result if still fresh"""
        info = self._get_installation_info()
        
        if not info or not info.last_validation_at:
            return None
        
        # Check if cache is still fresh
        cache_age = (datetime.utcnow() - info.last_validation_at).total_seconds()
        if cache_age > self.VALIDATION_CACHE_SECONDS:
            return None
        
        # Return cached result if license key matches
        if info.license_key == license_key and info.last_validation_result:
            return {
                'valid': True,
                'customer_email': info.license_customer_email,
                'customer_name': info.license_customer_name,
                'features': info.license_features or [],
                'expires_at': info.license_expires_at,
                'max_users': info.license_max_users,
                'days_remaining': (info.license_expires_at - datetime.utcnow()).days if info.license_expires_at else 0,
                'cached': True
            }
        
        return None
    
    def _cache_validation(self, license_key: str, result: Dict):
        """Cache validation result"""
        info = self._get_installation_info()
        if info:
            info.last_validation_at = datetime.utcnow()
            info.last_validation_result = result['valid']
            info.license_features = result.get('features')
            info.license_customer_email = result.get('customer_email')
            info.license_customer_name = result.get('customer_name')
            info.license_expires_at = result.get('expires_at')
            info.license_max_users = result.get('max_users')
            self.db.commit()
    
    def _log_validation(self, license_key: Optional[str], success: bool, error: Optional[str]):
        """Log validation attempt"""
        try:
            log = LicenseValidationLog(
                license_key_preview=license_key[:50] if license_key else None,
                validation_result=success,
                error_message=error
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log validation: {e}")
    
    def _get_installation_info(self) -> Optional[InstallationInfo]:
        """Get or create installation info"""
        info = self.db.query(InstallationInfo).first()
        
        if not info:
            # First time - create installation record
            info = InstallationInfo(
                installation_id=str(uuid.uuid4()),
                first_started_at=datetime.utcnow(),
                trial_started_at=datetime.utcnow(),
                trial_ends_at=datetime.utcnow() + timedelta(days=self.TRIAL_DAYS)
            )
            self.db.add(info)
            self.db.commit()
            logger.info(f"New installation created: {info.installation_id}, trial ends: {info.trial_ends_at}")
        
        return info
    
    def is_trial_active(self) -> bool:
        """Check if trial period is still active"""
        info = self._get_installation_info()
        
        if not info:
            return False
        
        # If has license, not in trial
        if info.license_key:
            return False
        
        # Check if trial period has ended
        return datetime.utcnow() < info.trial_ends_at
    
    def get_trial_status(self) -> Dict:
        """Get detailed trial status"""
        info = self._get_installation_info()
        now = datetime.utcnow()
        
        if not info:
            return {'status': 'unknown'}
        
        # Has license
        if info.license_key:
            license_result = self.verify_license(info.license_key)
            if license_result['valid']:
                return {
                    'status': 'licensed',
                    'has_license': True,
                    'features': license_result['features'],
                    'expires_at': license_result['expires_at'],
                    'days_remaining': license_result['days_remaining'],
                    'customer_name': license_result['customer_name']
                }
            else:
                # License invalid, fall through to trial/expired check
                pass
        
        # Check trial
        days_remaining = (info.trial_ends_at - now).days
        
        if days_remaining > 0:
            return {
                'status': 'trial',
                'days_remaining': days_remaining,
                'trial_ends_at': info.trial_ends_at,
                'in_grace_period': False
            }
        
        # Trial expired, check grace period
        grace_ends_at = info.trial_ends_at + timedelta(days=self.GRACE_PERIOD_DAYS)
        grace_days_remaining = (grace_ends_at - now).days
        
        if grace_days_remaining > 0:
            return {
                'status': 'grace_period',
                'days_remaining': grace_days_remaining,
                'grace_ends_at': grace_ends_at,
                'in_grace_period': True
            }
        
        # Fully expired
        return {
            'status': 'expired',
            'days_remaining': 0,
            'trial_expired': True,
            'expired_since': (now - grace_ends_at).days
        }
    
    def activate_license(self, license_key: str) -> Dict:
        """
        Activate a license key.
        
        Args:
            license_key: The license key to activate
        
        Returns:
            Dictionary with activation result
        """
        # Verify the license
        result = self.verify_license(license_key, skip_cache=True)
        
        if not result['valid']:
            return {
                'success': False,
                'error': result['error'],
                'message': result['message']
            }
        
        # Save license to database
        info = self._get_installation_info()
        info.license_key = license_key
        info.license_activated_at = datetime.utcnow()
        info.license_expires_at = result['expires_at']
        info.license_features = result['features']
        info.license_customer_email = result['customer_email']
        info.license_customer_name = result['customer_name']
        info.license_max_users = result.get('max_users')
        self.db.commit()
        
        logger.info(f"License activated for {result['customer_email']}")
        
        return {
            'success': True,
            'message': 'License activated successfully',
            'features': result['features'],
            'expires_at': result['expires_at'],
            'days_remaining': result['days_remaining']
        }
    
    def deactivate_license(self) -> Dict:
        """Remove the current license"""
        info = self._get_installation_info()
        if info:
            info.license_key = None
            info.license_activated_at = None
            info.license_expires_at = None
            info.license_features = None
            self.db.commit()
        
        return {'success': True, 'message': 'License deactivated'}
    
    def get_enabled_features(self) -> List[str]:
        """
        Get list of enabled features based on license or trial.
        
        Returns:
            List of feature IDs that are enabled
        """
        # Check trial first
        if self.is_trial_active():
            return ['all']  # All features during trial
        
        # Check license
        info = self._get_installation_info()
        if info and info.license_key:
            result = self.verify_license(info.license_key)
            if result['valid']:
                return result['features']
        
        # No license, no trial = core features only
        return []
    
    def has_feature(self, feature_id: str) -> bool:
        """
        Check if a specific feature is enabled.
        
        Args:
            feature_id: The feature ID to check
        
        Returns:
            True if feature is enabled, False otherwise
        """
        enabled_features = self.get_enabled_features()
        
        # 'all' means all features (trial mode)
        if 'all' in enabled_features:
            return True
        
        return feature_id in enabled_features
```

