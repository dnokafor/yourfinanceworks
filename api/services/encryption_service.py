"""
Encryption Service for tenant database encryption.

This service provides AES-256-GCM encryption/decryption capabilities
with tenant-specific key management and PostgreSQL optimizations.
"""

import json
import logging
from typing import Dict, Optional, Any, Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64
from functools import lru_cache
import time
from threading import Lock

from api.config.encryption_config import EncryptionConfig
from api.services.key_management_service import KeyManagementService
from api.exceptions.encryption_exceptions import (
    EncryptionError,
    DecryptionError,
    KeyNotFoundError
)

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Service for encrypting and decrypting tenant data using AES-256-GCM.
    
    Features:
    - Tenant-specific encryption keys
    - JSON data encryption for PostgreSQL JSONB fields
    - Key caching for performance optimization
    - Thread-safe operations
    """
    
    def __init__(self, key_management_service: Optional[KeyManagementService] = None):
        self.config = EncryptionConfig()
        self.key_management = key_management_service or KeyManagementService()
        self._key_cache: Dict[int, bytes] = {}
        self._cache_timestamps: Dict[int, float] = {}
        self._cache_lock = Lock()
        
        # Initialize AESGCM cipher
        self.cipher_class = AESGCM
        
        logger.info("EncryptionService initialized with AES-256-GCM")
    
    def encrypt_data(self, data: str, tenant_id: int) -> str:
        """
        Encrypt string data for a specific tenant.
        
        Args:
            data: Plain text data to encrypt
            tenant_id: Tenant identifier for key selection
            
        Returns:
            Base64 encoded encrypted data with nonce
            
        Raises:
            EncryptionError: If encryption fails
            KeyNotFoundError: If tenant key not found
        """
        if not data:
            return ""
            
        try:
            # Get tenant-specific encryption key
            key = self.get_tenant_key(tenant_id)
            
            # Create cipher instance
            cipher = self.cipher_class(key)
            
            # Generate random nonce (12 bytes for GCM)
            nonce = os.urandom(12)
            
            # Encrypt data
            encrypted_data = cipher.encrypt(nonce, data.encode('utf-8'), None)
            
            # Combine nonce and encrypted data
            combined = nonce + encrypted_data
            
            # Return base64 encoded result
            return base64.b64encode(combined).decode('ascii')
            
        except Exception as e:
            logger.error(f"Encryption failed for tenant {tenant_id}: {str(e)}")
            raise EncryptionError(f"Failed to encrypt data: {str(e)}")
    
    def decrypt_data(self, encrypted_data: str, tenant_id: int) -> str:
        """
        Decrypt string data for a specific tenant.
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            tenant_id: Tenant identifier for key selection
            
        Returns:
            Decrypted plain text data
            
        Raises:
            DecryptionError: If decryption fails
            KeyNotFoundError: If tenant key not found
        """
        if not encrypted_data:
            return ""
            
        try:
            # Get tenant-specific encryption key
            key = self.get_tenant_key(tenant_id)
            
            # Create cipher instance
            cipher = self.cipher_class(key)
            
            # Decode base64 data
            combined = base64.b64decode(encrypted_data.encode('ascii'))
            
            # Extract nonce (first 12 bytes) and encrypted data
            nonce = combined[:12]
            ciphertext = combined[12:]
            
            # Decrypt data
            decrypted_data = cipher.decrypt(nonce, ciphertext, None)
            
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption failed for tenant {tenant_id}: {str(e)}")
            raise DecryptionError(f"Failed to decrypt data: {str(e)}")
    
    def encrypt_json(self, data: Dict[str, Any], tenant_id: int) -> str:
        """
        Encrypt JSON data for PostgreSQL JSONB fields.
        
        Args:
            data: Dictionary to encrypt
            tenant_id: Tenant identifier for key selection
            
        Returns:
            Base64 encoded encrypted JSON data
            
        Raises:
            EncryptionError: If encryption fails
        """
        if not data:
            return ""
            
        try:
            # Convert dict to JSON string
            json_string = json.dumps(data, separators=(',', ':'), sort_keys=True)
            
            # Encrypt the JSON string
            return self.encrypt_data(json_string, tenant_id)
            
        except Exception as e:
            logger.error(f"JSON encryption failed for tenant {tenant_id}: {str(e)}")
            raise EncryptionError(f"Failed to encrypt JSON data: {str(e)}")
    
    def decrypt_json(self, encrypted_data: str, tenant_id: int) -> Dict[str, Any]:
        """
        Decrypt JSON data from PostgreSQL JSONB fields.
        
        Args:
            encrypted_data: Base64 encoded encrypted JSON data
            tenant_id: Tenant identifier for key selection
            
        Returns:
            Decrypted dictionary
            
        Raises:
            DecryptionError: If decryption fails
        """
        if not encrypted_data:
            return {}
            
        try:
            # Decrypt the JSON string
            json_string = self.decrypt_data(encrypted_data, tenant_id)
            
            # Parse JSON back to dict
            return json.loads(json_string)
            
        except Exception as e:
            logger.error(f"JSON decryption failed for tenant {tenant_id}: {str(e)}")
            raise DecryptionError(f"Failed to decrypt JSON data: {str(e)}")
    
    def get_tenant_key(self, tenant_id: int) -> bytes:
        """
        Get or derive encryption key for a specific tenant with caching.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            32-byte encryption key for AES-256
            
        Raises:
            KeyNotFoundError: If tenant key cannot be retrieved
        """
        with self._cache_lock:
            # Check cache first
            current_time = time.time()
            
            if (tenant_id in self._key_cache and 
                tenant_id in self._cache_timestamps and
                current_time - self._cache_timestamps[tenant_id] < self.config.KEY_CACHE_TTL_SECONDS):
                return self._key_cache[tenant_id]
            
            try:
                # Get tenant key from key management service
                tenant_key_material = self.key_management.retrieve_tenant_key(tenant_id)
                
                # Derive encryption key using PBKDF2
                derived_key = self._derive_key(tenant_key_material, tenant_id)
                
                # Cache the derived key
                self._key_cache[tenant_id] = derived_key
                self._cache_timestamps[tenant_id] = current_time
                
                # Clean old cache entries
                self._cleanup_cache()
                
                return derived_key
                
            except Exception as e:
                logger.error(f"Failed to get tenant key for {tenant_id}: {str(e)}")
                raise KeyNotFoundError(f"Tenant key not found for tenant {tenant_id}")
    
    def _derive_key(self, key_material: str, tenant_id: int) -> bytes:
        """
        Derive encryption key from key material using PBKDF2.
        
        Args:
            key_material: Base key material
            tenant_id: Tenant ID used as salt component
            
        Returns:
            32-byte derived key
        """
        # Create salt from tenant ID and config salt
        salt = f"{self.config.KEY_DERIVATION_SALT}:{tenant_id}".encode('utf-8')
        
        # Use PBKDF2 for key derivation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits for AES-256
            salt=salt,
            iterations=self.config.KEY_DERIVATION_ITERATIONS,
        )
        
        return kdf.derive(key_material.encode('utf-8'))
    
    def _cleanup_cache(self):
        """Clean up expired cache entries."""
        current_time = time.time()
        expired_keys = [
            tenant_id for tenant_id, timestamp in self._cache_timestamps.items()
            if current_time - timestamp >= self.config.KEY_CACHE_TTL_SECONDS
        ]
        
        for tenant_id in expired_keys:
            self._key_cache.pop(tenant_id, None)
            self._cache_timestamps.pop(tenant_id, None)
    
    def rotate_tenant_key(self, tenant_id: int) -> bool:
        """
        Rotate encryption key for a specific tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            True if rotation successful
            
        Raises:
            EncryptionError: If key rotation fails
        """
        try:
            # Clear cached key
            with self._cache_lock:
                self._key_cache.pop(tenant_id, None)
                self._cache_timestamps.pop(tenant_id, None)
            
            # Delegate to key management service
            success = self.key_management.rotate_key(tenant_id)
            
            if success:
                logger.info(f"Successfully rotated key for tenant {tenant_id}")
            else:
                logger.error(f"Failed to rotate key for tenant {tenant_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Key rotation failed for tenant {tenant_id}: {str(e)}")
            raise EncryptionError(f"Failed to rotate key: {str(e)}")
    
    def clear_cache(self, tenant_id: Optional[int] = None):
        """
        Clear encryption key cache.
        
        Args:
            tenant_id: Specific tenant to clear, or None for all
        """
        with self._cache_lock:
            if tenant_id is not None:
                self._key_cache.pop(tenant_id, None)
                self._cache_timestamps.pop(tenant_id, None)
                logger.info(f"Cleared cache for tenant {tenant_id}")
            else:
                self._key_cache.clear()
                self._cache_timestamps.clear()
                logger.info("Cleared all encryption key cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._cache_lock:
            return {
                "cached_keys": len(self._key_cache),
                "cache_size_bytes": sum(len(key) for key in self._key_cache.values()),
                "oldest_entry_age": (
                    time.time() - min(self._cache_timestamps.values())
                    if self._cache_timestamps else 0
                )
            }


# Global encryption service instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """
    Get global encryption service instance.
    
    Returns:
        EncryptionService instance
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service