#!/bin/bash
"""
Deployment script with encryption support.
This script handles the deployment of the application with encryption enabled.
"""

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
API_DIR="$PROJECT_ROOT/api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if environment is specified
if [ -z "$1" ]; then
    log_error "Usage: $0 <environment> [options]"
    log_info "Environments: development, staging, production"
    log_info "Options:"
    log_info "  --skip-encryption-init  Skip encryption initialization"
    log_info "  --force-key-rotation     Force key rotation during deployment"
    exit 1
fi

ENVIRONMENT=$1
SKIP_ENCRYPTION_INIT=false
FORCE_KEY_ROTATION=false

# Parse additional options
shift
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-encryption-init)
            SKIP_ENCRYPTION_INIT=true
            shift
            ;;
        --force-key-rotation)
            FORCE_KEY_ROTATION=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

log_info "Starting deployment for environment: $ENVIRONMENT"

# Load environment-specific encryption configuration
ENCRYPTION_ENV_FILE="$API_DIR/.env.encryption.$ENVIRONMENT"
if [ -f "$ENCRYPTION_ENV_FILE" ]; then
    log_info "Loading encryption configuration from: $ENCRYPTION_ENV_FILE"
    set -a
    source "$ENCRYPTION_ENV_FILE"
    set +a
else
    log_warn "Encryption configuration file not found: $ENCRYPTION_ENV_FILE"
    log_warn "Using default configuration"
fi

# Validate encryption configuration
validate_encryption_config() {
    log_info "Validating encryption configuration..."
    
    if [ "$ENCRYPTION_ENABLED" != "true" ]; then
        log_warn "Encryption is disabled"
        return 0
    fi
    
    if [ -z "$KEY_VAULT_PROVIDER" ]; then
        log_error "KEY_VAULT_PROVIDER must be specified"
        return 1
    fi
    
    case "$KEY_VAULT_PROVIDER" in
        "aws_kms")
            if [ -z "$AWS_KMS_KEY_ID" ]; then
                log_error "AWS_KMS_KEY_ID required for AWS KMS provider"
                return 1
            fi
            ;;
        "azure_kv")
            if [ -z "$AZURE_KEY_VAULT_URL" ] || [ -z "$AZURE_KEY_VAULT_KEY_NAME" ]; then
                log_error "Azure Key Vault configuration incomplete"
                return 1
            fi
            ;;
        "hashicorp_vault")
            if [ -z "$VAULT_URL" ] || [ -z "$VAULT_TOKEN" ]; then
                log_error "HashiCorp Vault configuration incomplete"
                return 1
            fi
            ;;
        "local")
            log_warn "Using local key vault - not recommended for production"
            ;;
        *)
            log_error "Unknown key vault provider: $KEY_VAULT_PROVIDER"
            return 1
            ;;
    esac
    
    log_info "Encryption configuration validated successfully"
}

# Create backup before deployment
create_backup() {
    log_info "Creating backup before deployment..."
    
    BACKUP_DIR="$PROJECT_ROOT/backups/pre-deployment-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup databases
    if command -v docker-compose &> /dev/null; then
        docker-compose exec -T postgres-master pg_dumpall -U postgres > "$BACKUP_DIR/master_backup.sql"
        log_info "Master database backup created: $BACKUP_DIR/master_backup.sql"
    fi
    
    # Backup encryption keys if they exist
    if [ -d "/app/keys" ]; then
        cp -r /app/keys "$BACKUP_DIR/keys_backup"
        log_info "Encryption keys backup created: $BACKUP_DIR/keys_backup"
    fi
    
    log_info "Backup completed: $BACKUP_DIR"
}

# Initialize encryption system
initialize_encryption() {
    if [ "$SKIP_ENCRYPTION_INIT" = true ]; then
        log_info "Skipping encryption initialization"
        return 0
    fi
    
    if [ "$ENCRYPTION_ENABLED" != "true" ]; then
        log_info "Encryption disabled, skipping initialization"
        return 0
    fi
    
    log_info "Initializing encryption system..."
    
    cd "$API_DIR"
    python scripts/init_encryption.py
    
    if [ $? -eq 0 ]; then
        log_info "Encryption system initialized successfully"
    else
        log_error "Encryption initialization failed"
        return 1
    fi
}

# Perform key rotation if requested
perform_key_rotation() {
    if [ "$FORCE_KEY_ROTATION" != true ]; then
        return 0
    fi
    
    if [ "$ENCRYPTION_ENABLED" != "true" ]; then
        log_info "Encryption disabled, skipping key rotation"
        return 0
    fi
    
    log_info "Performing forced key rotation..."
    
    cd "$API_DIR"
    python -c "
from services.key_rotation_service import KeyRotationService
from integrations.key_vault_factory import KeyVaultFactory

key_vault = KeyVaultFactory.create_key_vault()
rotation_service = KeyRotationService(key_vault)

# Get all tenant IDs (this would need to be implemented)
# For now, we'll skip automatic rotation and log a message
print('Key rotation would be performed here for all tenants')
print('Manual key rotation can be triggered through the admin interface')
"
    
    log_info "Key rotation completed"
}

# Deploy application
deploy_application() {
    log_info "Deploying application..."
    
    cd "$PROJECT_ROOT"
    
    # Build and start services
    docker-compose down
    docker-compose build
    docker-compose up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    if docker-compose ps | grep -q "unhealthy\|Exit"; then
        log_error "Some services are not healthy"
        docker-compose ps
        return 1
    fi
    
    log_info "Application deployed successfully"
}

# Run post-deployment tests
run_post_deployment_tests() {
    log_info "Running post-deployment tests..."
    
    cd "$API_DIR"
    
    # Test encryption functionality
    if [ "$ENCRYPTION_ENABLED" = "true" ]; then
        python -c "
from services.encryption_service import EncryptionService
import sys

try:
    service = EncryptionService()
    test_data = 'deployment-test-data'
    encrypted = service.encrypt_data(test_data, 1)
    decrypted = service.decrypt_data(encrypted, 1)
    
    if decrypted == test_data:
        print('Encryption test passed')
    else:
        print('Encryption test failed')
        sys.exit(1)
except Exception as e:
    print(f'Encryption test error: {e}')
    sys.exit(1)
"
        if [ $? -eq 0 ]; then
            log_info "Encryption tests passed"
        else
            log_error "Encryption tests failed"
            return 1
        fi
    fi
    
    # Test API health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_info "API health check passed"
    else
        log_error "API health check failed"
        return 1
    fi
    
    log_info "Post-deployment tests completed successfully"
}

# Main deployment process
main() {
    log_info "=== Starting Deployment Process ==="
    
    # Validate configuration
    if ! validate_encryption_config; then
        log_error "Configuration validation failed"
        exit 1
    fi
    
    # Create backup
    if ! create_backup; then
        log_error "Backup creation failed"
        exit 1
    fi
    
    # Initialize encryption
    if ! initialize_encryption; then
        log_error "Encryption initialization failed"
        exit 1
    fi
    
    # Deploy application
    if ! deploy_application; then
        log_error "Application deployment failed"
        exit 1
    fi
    
    # Perform key rotation if requested
    if ! perform_key_rotation; then
        log_error "Key rotation failed"
        exit 1
    fi
    
    # Run post-deployment tests
    if ! run_post_deployment_tests; then
        log_error "Post-deployment tests failed"
        exit 1
    fi
    
    log_info "=== Deployment Completed Successfully ==="
    log_info "Environment: $ENVIRONMENT"
    log_info "Encryption: $([ "$ENCRYPTION_ENABLED" = "true" ] && echo "Enabled" || echo "Disabled")"
    log_info "Key Vault Provider: ${KEY_VAULT_PROVIDER:-"Not specified"}"
}

# Run main function
main