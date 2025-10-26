"""
AWS KMS Key Vault Provider for Tenant Database Encryption

This module provides AWS KMS integration for secure key management
in the tenant database encryption system.
"""

import boto3
import base64
import json
import logging
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError, BotoCoreError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from encryption_config import EncryptionConfig
from exceptions.encryption_exceptions import (
    KeyNotFoundError,
    EncryptionError,
    KeyRotationError
)

logger = logging.getLogger(__name__)


class AWSKMSProvider:
    """AWS KMS provider for encryption key management."""
    
    def __init__(self, config: EncryptionConfig):
        """Initialize AWS KMS provider with configuration."""
        self.config = config
        self.region = config.AWS_REGION
        self.master_key_id = config.AWS_KMS_MASTER_KEY_ID
        
        # Initialize KMS client with IAM role-based authentication
        try:
            self.kms_client = boto3.client(
                'kms',
                region_name=self.region,
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
            )
            logger.info(f"AWS KMS client initialized for region: {self.region}")
        except Exception as e:
            logger.error(f"Failed to initialize AWS KMS client: {str(e)}")
            raise EncryptionError(f"AWS KMS initialization failed: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ClientError, BotoCoreError))
    )
    def generate_data_key(self, tenant_id: int, key_spec: str = "AES_256") -> Dict[str, str]:
        """
        Generate a new data encryption key for a tenant using AWS KMS.
        
        Args:
            tenant_id: Unique identifier for the tenant
            key_spec: Key specification (AES_256, AES_128)
            
        Returns:
            Dictionary containing plaintext and encrypted data keys
            
        Raises:
            EncryptionError: If key generation fails
        """
        try:
            # Create encryption context for audit and access control
            encryption_context = {
                'tenant_id': str(tenant_id),
                'purpose': 'database_encryption',
                'service': 'invoice_management'
            }
            
            response = self.kms_client.generate_data_key(
                KeyId=self.master_key_id,
                KeySpec=key_spec,
                EncryptionContext=encryption_context
            )
            
            # Return base64 encoded keys for storage
            return {
                'plaintext_key': base64.b64encode(response['Plaintext']).decode('utf-8'),
                'encrypted_key': base64.b64encode(response['CiphertextBlob']).decode('utf-8'),
                'key_id': response['KeyId']
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"AWS KMS generate_data_key failed for tenant {tenant_id}: {error_code}")
            raise EncryptionError(f"Failed to generate data key: {error_code}")
        except Exception as e:
            logger.error(f"Unexpected error generating data key for tenant {tenant_id}: {str(e)}")
            raise EncryptionError(f"Data key generation failed: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ClientError, BotoCoreError))
    )
    def decrypt_data_key(self, encrypted_key: str, tenant_id: int) -> str:
        """
        Decrypt an encrypted data key using AWS KMS.
        
        Args:
            encrypted_key: Base64 encoded encrypted data key
            tenant_id: Unique identifier for the tenant
            
        Returns:
            Base64 encoded plaintext data key
            
        Raises:
            KeyNotFoundError: If key cannot be found or decrypted
            EncryptionError: If decryption fails
        """
        try:
            # Decode the encrypted key
            encrypted_blob = base64.b64decode(encrypted_key.encode('utf-8'))
            
            # Create encryption context for verification
            encryption_context = {
                'tenant_id': str(tenant_id),
                'purpose': 'database_encryption',
                'service': 'invoice_management'
            }
            
            response = self.kms_client.decrypt(
                CiphertextBlob=encrypted_blob,
                EncryptionContext=encryption_context
            )
            
            return base64.b64encode(response['Plaintext']).decode('utf-8')
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['InvalidCiphertextException', 'KeyUnavailableException']:
                logger.error(f"Key not found or invalid for tenant {tenant_id}: {error_code}")
                raise KeyNotFoundError(f"Cannot decrypt key for tenant {tenant_id}: {error_code}")
            else:
                logger.error(f"AWS KMS decrypt failed for tenant {tenant_id}: {error_code}")
                raise EncryptionError(f"Key decryption failed: {error_code}")
        except Exception as e:
            logger.error(f"Unexpected error decrypting key for tenant {tenant_id}: {str(e)}")
            raise EncryptionError(f"Key decryption failed: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ClientError, BotoCoreError))
    )
    def rotate_master_key(self) -> bool:
        """
        Rotate the AWS KMS master key.
        
        Returns:
            True if rotation was successful
            
        Raises:
            KeyRotationError: If rotation fails
        """
        try:
            # Enable automatic key rotation
            self.kms_client.enable_key_rotation(KeyId=self.master_key_id)
            
            # Get rotation status to verify
            response = self.kms_client.get_key_rotation_status(KeyId=self.master_key_id)
            
            if response['KeyRotationEnabled']:
                logger.info(f"Key rotation enabled for master key: {self.master_key_id}")
                return True
            else:
                raise KeyRotationError("Failed to enable key rotation")
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"AWS KMS key rotation failed: {error_code}")
            raise KeyRotationError(f"Master key rotation failed: {error_code}")
        except Exception as e:
            logger.error(f"Unexpected error during key rotation: {str(e)}")
            raise KeyRotationError(f"Key rotation failed: {str(e)}")
    
    def create_key_alias(self, tenant_id: int) -> str:
        """
        Create a key alias for a tenant.
        
        Args:
            tenant_id: Unique identifier for the tenant
            
        Returns:
            Key alias string
        """
        return f"alias/tenant-{tenant_id}-encryption-key"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ClientError, BotoCoreError))
    )
    def create_tenant_key(self, tenant_id: int, description: Optional[str] = None) -> str:
        """
        Create a dedicated KMS key for a tenant.
        
        Args:
            tenant_id: Unique identifier for the tenant
            description: Optional description for the key
            
        Returns:
            Key ID of the created key
            
        Raises:
            EncryptionError: If key creation fails
        """
        try:
            if not description:
                description = f"Encryption key for tenant {tenant_id}"
            
            # Create the key
            response = self.kms_client.create_key(
                Description=description,
                Usage='ENCRYPT_DECRYPT',
                KeySpec='SYMMETRIC_DEFAULT',
                Origin='AWS_KMS',
                Tags=[
                    {
                        'TagKey': 'TenantId',
                        'TagValue': str(tenant_id)
                    },
                    {
                        'TagKey': 'Purpose',
                        'TagValue': 'DatabaseEncryption'
                    },
                    {
                        'TagKey': 'Service',
                        'TagValue': 'InvoiceManagement'
                    }
                ]
            )
            
            key_id = response['KeyMetadata']['KeyId']
            
            # Create an alias for easier management
            alias = self.create_key_alias(tenant_id)
            try:
                self.kms_client.create_alias(
                    AliasName=alias,
                    TargetKeyId=key_id
                )
                logger.info(f"Created key alias {alias} for tenant {tenant_id}")
            except ClientError as e:
                if e.response['Error']['Code'] != 'AlreadyExistsException':
                    logger.warning(f"Failed to create alias {alias}: {e}")
            
            logger.info(f"Created KMS key {key_id} for tenant {tenant_id}")
            return key_id
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"AWS KMS key creation failed for tenant {tenant_id}: {error_code}")
            raise EncryptionError(f"Failed to create tenant key: {error_code}")
        except Exception as e:
            logger.error(f"Unexpected error creating key for tenant {tenant_id}: {str(e)}")
            raise EncryptionError(f"Tenant key creation failed: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ClientError, BotoCoreError))
    )
    def get_key_info(self, key_id: str) -> Dict[str, Any]:
        """
        Get information about a KMS key.
        
        Args:
            key_id: KMS key ID or alias
            
        Returns:
            Dictionary containing key metadata
            
        Raises:
            KeyNotFoundError: If key is not found
            EncryptionError: If operation fails
        """
        try:
            response = self.kms_client.describe_key(KeyId=key_id)
            return response['KeyMetadata']
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotFoundException':
                raise KeyNotFoundError(f"KMS key not found: {key_id}")
            else:
                logger.error(f"Failed to get key info for {key_id}: {error_code}")
                raise EncryptionError(f"Failed to get key info: {error_code}")
        except Exception as e:
            logger.error(f"Unexpected error getting key info for {key_id}: {str(e)}")
            raise EncryptionError(f"Get key info failed: {str(e)}")
    
    def audit_key_access(self, tenant_id: int, operation: str, key_id: str, success: bool) -> None:
        """
        Log key access for audit purposes.
        
        Args:
            tenant_id: Unique identifier for the tenant
            operation: Operation performed (generate, decrypt, rotate, etc.)
            key_id: KMS key ID
            success: Whether the operation was successful
        """
        audit_data = {
            'provider': 'aws_kms',
            'tenant_id': tenant_id,
            'operation': operation,
            'key_id': key_id,
            'success': success,
            'region': self.region
        }
        
        if success:
            logger.info(f"AWS KMS audit: {json.dumps(audit_data)}")
        else:
            logger.warning(f"AWS KMS audit (failed): {json.dumps(audit_data)}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the AWS KMS connection.
        
        Returns:
            Dictionary containing health status
        """
        try:
            # Try to describe the master key
            response = self.kms_client.describe_key(KeyId=self.master_key_id)
            
            return {
                'provider': 'aws_kms',
                'status': 'healthy',
                'region': self.region,
                'master_key_id': self.master_key_id,
                'key_state': response['KeyMetadata']['KeyState']
            }
            
        except Exception as e:
            return {
                'provider': 'aws_kms',
                'status': 'unhealthy',
                'region': self.region,
                'error': str(e)
            }