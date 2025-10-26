"""
Key Vault Factory for Tenant Database Encryption

This module provides a factory pattern for creating different key vault providers
based on configuration settings.
"""

import logging
from typing import Union, Dict, Any
from enum import Enum

from config.encryption_config import EncryptionConfig
from exceptions.encryption_exceptions import EncryptionError

# Import key vault providers
from .aws_kms_provider import AWSKMSProvider
from .azure_keyvault_provider import AzureKeyVaultProvider
from .hashicorp_vault_provider import HashiCorpVaultProvider

logger = logging.getLogger(__name__)


class KeyVaultProvider(Enum):
    """Enumeration of supported key vault providers."""
    LOCAL = "local"
    AWS_KMS = "aws_kms"
    AZURE_KEYVAULT = "azure_keyvault"
    HASHICORP_VAULT = "hashicorp_vault"


class KeyVaultFactory:
    """Factory class for creating key vault provider instances."""
    
    _providers = {
        KeyVaultProvider.AWS_KMS: AWSKMSProvider,
        KeyVaultProvider.AZURE_KEYVAULT: AzureKeyVaultProvider,
        KeyVaultProvider.HASHICORP_VAULT: HashiCorpVaultProvider,
    }
    
    @classmethod
    def create_provider(cls, config: EncryptionConfig) -> Union[AWSKMSProvider, AzureKeyVaultProvider, HashiCorpVaultProvider]:
        """
        Create a key vault provider instance based on configuration.
        
        Args:
            config: Encryption configuration object
            
        Returns:
            Key vault provider instance
            
        Raises:
            EncryptionError: If provider type is unsupported or initialization fails
        """
        try:
            provider_type = KeyVaultProvider(config.KEY_VAULT_PROVIDER.lower())
        except ValueError:
            raise EncryptionError(f"Unsupported key vault provider: {config.KEY_VAULT_PROVIDER}")
        
        if provider_type == KeyVaultProvider.LOCAL:
            # Local provider is handled by the key management service directly
            raise EncryptionError("Local provider should be handled by KeyManagementService")
        
        if provider_type not in cls._providers:
            raise EncryptionError(f"Provider {provider_type.value} not implemented")
        
        try:
            provider_class = cls._providers[provider_type]
            provider_instance = provider_class(config)
            
            logger.info(f"Created key vault provider: {provider_type.value}")
            return provider_instance
            
        except Exception as e:
            logger.error(f"Failed to create provider {provider_type.value}: {str(e)}")
            raise EncryptionError(f"Provider initialization failed: {str(e)}")
    
    @classmethod
    def get_supported_providers(cls) -> Dict[str, str]:
        """
        Get a dictionary of supported providers and their descriptions.
        
        Returns:
            Dictionary mapping provider names to descriptions
        """
        return {
            KeyVaultProvider.LOCAL.value: "Local file-based key storage (development only)",
            KeyVaultProvider.AWS_KMS.value: "Amazon Web Services Key Management Service",
            KeyVaultProvider.AZURE_KEYVAULT.value: "Microsoft Azure Key Vault",
            KeyVaultProvider.HASHICORP_VAULT.value: "HashiCorp Vault"
        }
    
    @classmethod
    def validate_provider_config(cls, config: EncryptionConfig) -> Dict[str, Any]:
        """
        Validate the configuration for the specified provider.
        
        Args:
            config: Encryption configuration object
            
        Returns:
            Dictionary containing validation results
        """
        try:
            provider_type = KeyVaultProvider(config.KEY_VAULT_PROVIDER.lower())
        except ValueError:
            return {
                'valid': False,
                'provider': config.KEY_VAULT_PROVIDER,
                'errors': [f"Unsupported provider: {config.KEY_VAULT_PROVIDER}"]
            }
        
        errors = []
        warnings = []
        
        # Validate provider-specific configuration
        if provider_type == KeyVaultProvider.AWS_KMS:
            if not config.AWS_REGION:
                errors.append("AWS_REGION is required for AWS KMS")
            if not config.AWS_KMS_MASTER_KEY_ID:
                errors.append("AWS_KMS_MASTER_KEY_ID is required for AWS KMS")
            if not config.AWS_ACCESS_KEY_ID and not config.AWS_SECRET_ACCESS_KEY:
                warnings.append("AWS credentials not configured, will use IAM role or default credential chain")
        
        elif provider_type == KeyVaultProvider.AZURE_KEYVAULT:
            if not config.AZURE_KEYVAULT_URL:
                errors.append("AZURE_KEYVAULT_URL is required for Azure Key Vault")
            if not config.AZURE_TENANT_ID:
                warnings.append("AZURE_TENANT_ID not configured, will use default credential")
            if not config.AZURE_CLIENT_ID or not config.AZURE_CLIENT_SECRET:
                warnings.append("Azure service principal not configured, will use default credential")
        
        elif provider_type == KeyVaultProvider.HASHICORP_VAULT:
            if not config.HASHICORP_VAULT_URL:
                errors.append("HASHICORP_VAULT_URL is required for HashiCorp Vault")
            if not config.HASHICORP_VAULT_TOKEN:
                errors.append("HASHICORP_VAULT_TOKEN is required for HashiCorp Vault")
        
        return {
            'valid': len(errors) == 0,
            'provider': provider_type.value,
            'errors': errors,
            'warnings': warnings
        }
    
    @classmethod
    def test_provider_connection(cls, config: EncryptionConfig) -> Dict[str, Any]:
        """
        Test the connection to the configured key vault provider.
        
        Args:
            config: Encryption configuration object
            
        Returns:
            Dictionary containing connection test results
        """
        try:
            # Validate configuration first
            validation = cls.validate_provider_config(config)
            if not validation['valid']:
                return {
                    'success': False,
                    'provider': validation['provider'],
                    'error': 'Configuration validation failed',
                    'details': validation['errors']
                }
            
            # Create provider instance
            provider = cls.create_provider(config)
            
            # Perform health check
            health_status = provider.health_check()
            
            return {
                'success': health_status['status'] == 'healthy',
                'provider': health_status['provider'],
                'health_status': health_status,
                'warnings': validation.get('warnings', [])
            }
            
        except Exception as e:
            logger.error(f"Provider connection test failed: {str(e)}")
            return {
                'success': False,
                'provider': config.KEY_VAULT_PROVIDER,
                'error': str(e)
            }


class KeyVaultInterface:
    """
    Abstract interface for key vault operations.
    
    This class defines the common interface that all key vault providers should implement.
    """
    
    def generate_data_key(self, tenant_id: int, **kwargs) -> Dict[str, str]:
        """Generate a new data encryption key for a tenant."""
        raise NotImplementedError
    
    def decrypt_data_key(self, encrypted_key: str, tenant_id: int) -> str:
        """Decrypt an encrypted data key."""
        raise NotImplementedError
    
    def rotate_tenant_key(self, tenant_id: int) -> Dict[str, str]:
        """Rotate a tenant's encryption key."""
        raise NotImplementedError
    
    def get_key_info(self, key_identifier: str) -> Dict[str, Any]:
        """Get information about a key."""
        raise NotImplementedError
    
    def audit_key_access(self, tenant_id: int, operation: str, key_id: str, success: bool) -> None:
        """Log key access for audit purposes."""
        raise NotImplementedError
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the provider."""
        raise NotImplementedError


# Ensure all providers implement the interface
def _validate_provider_interface():
    """Validate that all providers implement the required interface methods."""
    interface_methods = [method for method in dir(KeyVaultInterface) 
                        if not method.startswith('_') and callable(getattr(KeyVaultInterface, method))]
    
    for provider_enum, provider_class in KeyVaultFactory._providers.items():
        provider_methods = [method for method in dir(provider_class) 
                           if not method.startswith('_') and callable(getattr(provider_class, method))]
        
        missing_methods = set(interface_methods) - set(provider_methods)
        if missing_methods:
            logger.warning(f"Provider {provider_enum.value} missing interface methods: {missing_methods}")


# Validate interfaces on module import
_validate_provider_interface()