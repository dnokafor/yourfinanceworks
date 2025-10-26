#!/usr/bin/env python3
"""
Check encryption environment variables between containers.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Check encryption environment variables."""
    logger.info("=== Checking encryption environment variables ===")
    
    # Key environment variables that affect encryption
    env_vars = [
        "ENCRYPTION_ENABLED",
        "ENCRYPTION_ALGORITHM", 
        "KEY_VAULT_PROVIDER",
        "MASTER_KEY_ID",
        "MASTER_KEY_PATH",
        "KEY_DERIVATION_ITERATIONS",
        "KEY_DERIVATION_SALT",
        "KEY_CACHE_TTL_SECONDS",
        "DATABASE_TYPE",
        "POSTGRES_JSONB_ENCRYPTION",
    ]
    
    logger.info("Environment variables:")
    for var in env_vars:
        value = os.getenv(var, "NOT_SET")
        logger.info(f"  {var}: {value}")
    
    # Also check the encryption config object
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from encryption_config import EncryptionConfig
        
        config = EncryptionConfig()
        logger.info("\nEncryption config values:")
        logger.info(f"  ENCRYPTION_ENABLED: {config.ENCRYPTION_ENABLED}")
        logger.info(f"  ENCRYPTION_ALGORITHM: {config.ENCRYPTION_ALGORITHM}")
        logger.info(f"  KEY_VAULT_PROVIDER: {config.KEY_VAULT_PROVIDER}")
        logger.info(f"  MASTER_KEY_ID: {config.MASTER_KEY_ID}")
        logger.info(f"  MASTER_KEY_PATH: {config.MASTER_KEY_PATH}")
        logger.info(f"  KEY_DERIVATION_ITERATIONS: {config.KEY_DERIVATION_ITERATIONS}")
        logger.info(f"  KEY_DERIVATION_SALT: {config.KEY_DERIVATION_SALT}")
        logger.info(f"  KEY_CACHE_TTL_SECONDS: {config.KEY_CACHE_TTL_SECONDS}")
        logger.info(f"  DATABASE_TYPE: {config.DATABASE_TYPE}")
        logger.info(f"  POSTGRES_JSONB_ENCRYPTION: {config.POSTGRES_JSONB_ENCRYPTION}")
        
    except Exception as e:
        logger.error(f"Failed to load encryption config: {e}")
    
    # Check container hostname to identify which container we're in
    hostname = os.getenv("HOSTNAME", "unknown")
    logger.info(f"\nContainer hostname: {hostname}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)