#!/usr/bin/env python3
"""
Encryption initialization script for production deployment.
This script sets up the encryption system during application startup.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from config.encryption_config import EncryptionConfig
from services.key_management_service import KeyManagementService
from services.encryption_service import EncryptionService
from integrations.key_vault_factory import KeyVaultFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_key_directory():
    """Ensure the encryption key directory exists."""
    key_dir = Path(EncryptionConfig.MASTER_KEY_PATH).parent
    key_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    logger.info(f"Ensured key directory exists: {key_dir}")


def initialize_master_key():
    """Initialize the master key if it doesn't exist."""
    try:
        key_vault = KeyVaultFactory.create_key_vault()
        key_management = KeyManagementService(key_vault)
        
        # Check if master key exists
        if not key_management.master_key_exists():
            logger.info("Master key not found, generating new master key...")
            key_management.generate_master_key()
            logger.info("Master key generated successfully")
        else:
            logger.info("Master key already exists")
            
        # Verify master key is accessible
        key_management.verify_master_key()
        logger.info("Master key verification successful")
        
    except Exception as e:
        logger.error(f"Failed to initialize master key: {e}")
        raise


def initialize_encryption_service():
    """Initialize and verify the encryption service."""
    try:
        encryption_service = EncryptionService()
        
        # Test encryption/decryption with a sample
        test_data = "test-encryption-data"
        test_tenant_id = 1
        
        encrypted = encryption_service.encrypt_data(test_data, test_tenant_id)
        decrypted = encryption_service.decrypt_data(encrypted, test_tenant_id)
        
        if decrypted != test_data:
            raise ValueError("Encryption service test failed")
            
        logger.info("Encryption service initialized and verified successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize encryption service: {e}")
        raise


def verify_configuration():
    """Verify encryption configuration is valid."""
    try:
        config = EncryptionConfig()
        
        # Check required configuration
        if not config.ENCRYPTION_ENABLED:
            logger.warning("Encryption is disabled")
            return
            
        if not config.KEY_VAULT_PROVIDER:
            raise ValueError("KEY_VAULT_PROVIDER must be specified")
            
        if not config.MASTER_KEY_ID:
            raise ValueError("MASTER_KEY_ID must be specified")
            
        # Validate key vault provider specific configuration
        if config.KEY_VAULT_PROVIDER == "aws_kms":
            if not os.getenv("AWS_KMS_KEY_ID"):
                raise ValueError("AWS_KMS_KEY_ID required for AWS KMS provider")
                
        elif config.KEY_VAULT_PROVIDER == "azure_kv":
            required_vars = ["AZURE_KEY_VAULT_URL", "AZURE_KEY_VAULT_KEY_NAME"]
            for var in required_vars:
                if not os.getenv(var):
                    raise ValueError(f"{var} required for Azure Key Vault provider")
                    
        elif config.KEY_VAULT_PROVIDER == "hashicorp_vault":
            required_vars = ["VAULT_URL", "VAULT_TOKEN"]
            for var in required_vars:
                if not os.getenv(var):
                    raise ValueError(f"{var} required for HashiCorp Vault provider")
        
        logger.info(f"Configuration verified for provider: {config.KEY_VAULT_PROVIDER}")
        
    except Exception as e:
        logger.error(f"Configuration verification failed: {e}")
        raise


def main():
    """Main initialization function."""
    try:
        logger.info("Starting encryption system initialization...")
        
        # Verify configuration
        verify_configuration()
        
        # Skip initialization if encryption is disabled
        if not EncryptionConfig.ENCRYPTION_ENABLED:
            logger.info("Encryption is disabled, skipping initialization")
            return
        
        # Ensure key directory exists
        ensure_key_directory()
        
        # Initialize master key
        initialize_master_key()
        
        # Initialize encryption service
        initialize_encryption_service()
        
        logger.info("Encryption system initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Encryption initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()