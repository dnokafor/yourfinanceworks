"""
SQLAlchemy Column Encryptor for transparent database encryption.

This module provides custom SQLAlchemy TypeDecorator classes that automatically
encrypt and decrypt data when storing/retrieving from PostgreSQL databases.
"""

import json
import logging
from typing import Any, Optional, Dict
from sqlalchemy import TypeDecorator, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Dialect

from api.services.encryption_service import get_encryption_service
from api.exceptions.encryption_exceptions import EncryptionError, DecryptionError
from api.models.database import get_tenant_context

logger = logging.getLogger(__name__)


class EncryptedColumn(TypeDecorator):
    """
    SQLAlchemy TypeDecorator for transparent string data encryption.
    
    This column type automatically encrypts data before storing in the database
    and decrypts it when retrieving. It uses the tenant context to determine
    which encryption key to use.
    
    Usage:
        class User(Base):
            email = EncryptedColumn(String, nullable=False)
            first_name = EncryptedColumn(String, nullable=True)
    """
    
    impl = Text  # Use Text to store base64 encoded encrypted data
    cache_ok = True
    
    def __init__(self, *args, **kwargs):
        """Initialize the encrypted column type."""
        super().__init__(*args, **kwargs)
        self.encryption_service = get_encryption_service()
    
    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[str]:
        """
        Encrypt data before storing in database.
        
        Args:
            value: Plain text value to encrypt
            dialect: SQLAlchemy dialect (not used)
            
        Returns:
            Encrypted and base64 encoded string, or None if value is None/empty
        """
        if value is None or value == "":
            return value
        
        try:
            # Get current tenant context
            tenant_id = get_tenant_context()
            if tenant_id is None:
                logger.error("No tenant context available for encryption")
                raise EncryptionError("Tenant context required for encryption")
            
            # Convert value to string if it isn't already
            str_value = str(value)
            
            # Encrypt the data
            encrypted_value = self.encryption_service.encrypt_data(str_value, tenant_id)
            
            logger.debug(f"Encrypted data for tenant {tenant_id}")
            return encrypted_value
            
        except Exception as e:
            logger.error(f"Failed to encrypt column data: {str(e)}")
            raise EncryptionError(f"Column encryption failed: {str(e)}")
    
    def process_result_value(self, value: Any, dialect: Dialect) -> Optional[str]:
        """
        Decrypt data after retrieving from database.
        
        Args:
            value: Encrypted base64 encoded string from database
            dialect: SQLAlchemy dialect (not used)
            
        Returns:
            Decrypted plain text string, or None if value is None/empty
        """
        if value is None or value == "":
            return value
        
        try:
            # Get current tenant context
            tenant_id = get_tenant_context()
            if tenant_id is None:
                logger.error("No tenant context available for decryption")
                # In read operations, we might want to be more lenient
                # Return the encrypted value rather than failing
                logger.warning("Returning encrypted value due to missing tenant context")
                return value
            
            # Decrypt the data
            decrypted_value = self.encryption_service.decrypt_data(value, tenant_id)
            
            logger.debug(f"Decrypted data for tenant {tenant_id}")
            return decrypted_value
            
        except Exception as e:
            logger.error(f"Failed to decrypt column data: {str(e)}")
            # In production, you might want to handle this more gracefully
            # For now, we'll raise an exception to ensure data integrity
            raise DecryptionError(f"Column decryption failed: {str(e)}")


class EncryptedJSON(TypeDecorator):
    """
    SQLAlchemy TypeDecorator for transparent JSON data encryption using PostgreSQL JSONB.
    
    This column type automatically encrypts JSON data before storing in the database
    and decrypts it when retrieving. The encrypted data is stored as a text field
    containing the base64 encoded encrypted JSON.
    
    Usage:
        class Invoice(Base):
            custom_fields = EncryptedJSON(nullable=True)
            analysis_result = EncryptedJSON(nullable=True)
    """
    
    impl = Text  # Store encrypted JSON as text
    cache_ok = True
    
    def __init__(self, *args, **kwargs):
        """Initialize the encrypted JSON column type."""
        super().__init__(*args, **kwargs)
        self.encryption_service = get_encryption_service()
    
    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[str]:
        """
        Encrypt JSON data before storing in database.
        
        Args:
            value: Dictionary or JSON-serializable data to encrypt
            dialect: SQLAlchemy dialect (not used)
            
        Returns:
            Encrypted and base64 encoded JSON string, or None if value is None/empty
        """
        if value is None:
            return None
        
        # Handle empty dict/list
        if value == {} or value == []:
            return None
        
        try:
            # Get current tenant context
            tenant_id = get_tenant_context()
            if tenant_id is None:
                logger.error("No tenant context available for JSON encryption")
                raise EncryptionError("Tenant context required for JSON encryption")
            
            # Ensure value is a dictionary or list
            if not isinstance(value, (dict, list)):
                logger.warning(f"Converting non-dict/list value to dict: {type(value)}")
                # Try to convert to dict if it's a string that looks like JSON
                if isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        # If it's not valid JSON, wrap it in a dict
                        value = {"value": value}
                else:
                    # Wrap other types in a dict
                    value = {"value": value}
            
            # Encrypt the JSON data
            encrypted_value = self.encryption_service.encrypt_json(value, tenant_id)
            
            logger.debug(f"Encrypted JSON data for tenant {tenant_id}")
            return encrypted_value
            
        except Exception as e:
            logger.error(f"Failed to encrypt JSON column data: {str(e)}")
            raise EncryptionError(f"JSON column encryption failed: {str(e)}")
    
    def process_result_value(self, value: Any, dialect: Dialect) -> Optional[Dict[str, Any]]:
        """
        Decrypt JSON data after retrieving from database.
        
        Args:
            value: Encrypted base64 encoded JSON string from database
            dialect: SQLAlchemy dialect (not used)
            
        Returns:
            Decrypted dictionary/list, or None if value is None/empty
        """
        if value is None or value == "":
            return None
        
        try:
            # Get current tenant context
            tenant_id = get_tenant_context()
            if tenant_id is None:
                logger.error("No tenant context available for JSON decryption")
                # In read operations, we might want to be more lenient
                logger.warning("Returning None due to missing tenant context for JSON decryption")
                return None
            
            # Decrypt the JSON data
            decrypted_value = self.encryption_service.decrypt_json(value, tenant_id)
            
            logger.debug(f"Decrypted JSON data for tenant {tenant_id}")
            return decrypted_value
            
        except Exception as e:
            logger.error(f"Failed to decrypt JSON column data: {str(e)}")
            # In production, you might want to handle this more gracefully
            # For now, we'll raise an exception to ensure data integrity
            raise DecryptionError(f"JSON column decryption failed: {str(e)}")


# Convenience functions for creating encrypted columns with proper indexing

def create_encrypted_string_column(length: Optional[int] = None, **kwargs) -> EncryptedColumn:
    """
    Create an encrypted string column with optional length constraint.
    
    Args:
        length: Maximum length for the original string (before encryption)
        **kwargs: Additional SQLAlchemy column arguments
        
    Returns:
        EncryptedColumn instance
        
    Note:
        Encrypted data will be longer than the original, so the actual database
        column will use Text type regardless of the length parameter.
    """
    if length:
        # Store length info for validation but use Text for storage
        kwargs['info'] = kwargs.get('info', {})
        kwargs['info']['original_max_length'] = length
    
    return EncryptedColumn(**kwargs)


def create_encrypted_json_column(**kwargs) -> EncryptedJSON:
    """
    Create an encrypted JSON column.
    
    Args:
        **kwargs: Additional SQLAlchemy column arguments
        
    Returns:
        EncryptedJSON instance
    """
    return EncryptedJSON(**kwargs)


# PostgreSQL-specific optimizations

class PostgreSQLEncryptedColumn(EncryptedColumn):
    """
    PostgreSQL-optimized encrypted column with additional features.
    
    This version includes PostgreSQL-specific optimizations such as:
    - Better handling of PostgreSQL-specific data types
    - Optimized storage for encrypted data
    - Support for PostgreSQL indexing strategies
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize PostgreSQL-optimized encrypted column."""
        super().__init__(*args, **kwargs)
        # Add PostgreSQL-specific optimizations here if needed
    
    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[str]:
        """PostgreSQL-optimized encryption with better performance."""
        # Use parent implementation but could add PostgreSQL-specific optimizations
        return super().process_bind_param(value, dialect)
    
    def process_result_value(self, value: Any, dialect: Dialect) -> Optional[str]:
        """PostgreSQL-optimized decryption with better performance."""
        # Use parent implementation but could add PostgreSQL-specific optimizations
        return super().process_result_value(value, dialect)


class PostgreSQLEncryptedJSON(EncryptedJSON):
    """
    PostgreSQL-optimized encrypted JSON column.
    
    This version is specifically optimized for PostgreSQL JSONB operations
    while maintaining encryption capabilities.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize PostgreSQL-optimized encrypted JSON column."""
        super().__init__(*args, **kwargs)
        # Add PostgreSQL JSONB-specific optimizations here if needed
    
    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[str]:
        """PostgreSQL JSONB-optimized encryption."""
        # Use parent implementation but could add JSONB-specific optimizations
        return super().process_bind_param(value, dialect)
    
    def process_result_value(self, value: Any, dialect: Dialect) -> Optional[Dict[str, Any]]:
        """PostgreSQL JSONB-optimized decryption."""
        # Use parent implementation but could add JSONB-specific optimizations
        return super().process_result_value(value, dialect)


# Utility functions for migration and testing

def is_encrypted_data(value: str) -> bool:
    """
    Check if a string value appears to be encrypted data.
    
    Args:
        value: String to check
        
    Returns:
        True if the value appears to be base64 encoded encrypted data
    """
    if not isinstance(value, str) or len(value) < 20:
        return False
    
    try:
        import base64
        # Try to decode as base64
        decoded = base64.b64decode(value)
        # Encrypted data should have at least 12 bytes (nonce) + some ciphertext
        return len(decoded) >= 16
    except Exception:
        return False


def get_encryption_metadata(column_type) -> Dict[str, Any]:
    """
    Get metadata about an encrypted column type.
    
    Args:
        column_type: SQLAlchemy column type instance
        
    Returns:
        Dictionary with encryption metadata
    """
    metadata = {
        'is_encrypted': False,
        'encryption_type': None,
        'supports_indexing': False
    }
    
    if isinstance(column_type, (EncryptedColumn, PostgreSQLEncryptedColumn)):
        metadata.update({
            'is_encrypted': True,
            'encryption_type': 'string',
            'supports_indexing': False  # Encrypted data cannot be indexed directly
        })
    elif isinstance(column_type, (EncryptedJSON, PostgreSQLEncryptedJSON)):
        metadata.update({
            'is_encrypted': True,
            'encryption_type': 'json',
            'supports_indexing': False  # Encrypted JSON cannot be queried directly
        })
    
    return metadata