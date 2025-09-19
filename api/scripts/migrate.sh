#!/bin/bash

# Migration management script for multi-tenant invoice application
# This script provides convenient commands for managing database migrations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$(dirname "$SCRIPT_DIR")"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  init                     Create initial migrations for master and tenant databases"
    echo "  setup                    Set up database schema by running migrations"
    echo "  create <message>         Create a new migration"
    echo "    --master               Create migration for master database (default)"
    echo "    --tenant               Create migration for tenant database"
    echo "  upgrade                  Upgrade database to latest version"
    echo "    --master               Upgrade master database (default)"
    echo "    --tenant <id>          Upgrade specific tenant database"
    echo "    --all-tenants          Upgrade all tenant databases"
    echo "    --revision <rev>       Upgrade to specific revision (default: head)"
    echo "  downgrade                Downgrade database"
    echo "    --master               Downgrade master database (default)"
    echo "    --tenant <id>          Downgrade specific tenant database"
    echo "    --revision <rev>       Downgrade to specific revision (default: -1)"
    echo "  current                  Show current database revision"
    echo "    --master               Show master database revision (default)"
    echo "    --tenant <id>          Show specific tenant database revision"
    echo "  history                  Show migration history"
    echo "    --master               Show master database history (default)"
    echo "    --tenant <id>          Show specific tenant database history"
    echo "  status                   Show status of all databases"
    echo ""
    echo "Examples:"
    echo "  $0 init                                    # Create initial migrations"
    echo "  $0 setup                                   # Set up database schema"
    echo "  $0 create \"Add user table\" --master        # Create master DB migration"
    echo "  $0 create \"Add invoice table\" --tenant     # Create tenant DB migration"
    echo "  $0 upgrade --master                        # Upgrade master database"
    echo "  $0 upgrade --tenant 1                      # Upgrade tenant 1 database"
    echo "  $0 upgrade --all-tenants                   # Upgrade all tenant databases"
    echo "  $0 current --tenant 2                      # Show current revision for tenant 2"
}

# Function to run Python migration script
run_migration_script() {
    cd "$API_DIR"
    python scripts/manage_migrations.py "$@"
}

# Parse command line arguments
COMMAND=""
DB_TYPE="master"
TENANT_ID=""
MESSAGE=""
REVISION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        init|setup|create|upgrade|downgrade|current|history|status)
            COMMAND="$1"
            shift
            ;;
        --master)
            DB_TYPE="master"
            shift
            ;;
        --tenant)
            DB_TYPE="tenant"
            if [[ $# -gt 1 && ! $2 =~ ^-- ]]; then
                TENANT_ID="$2"
                shift
            fi
            shift
            ;;
        --all-tenants)
            DB_TYPE="all"
            shift
            ;;
        --revision)
            if [[ $# -gt 1 ]]; then
                REVISION="$2"
                shift
            fi
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            if [[ -z "$MESSAGE" && "$COMMAND" == "create" ]]; then
                MESSAGE="$1"
            else
                print_error "Unknown option: $1"
                show_usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Check if command is provided
if [[ -z "$COMMAND" ]]; then
    print_error "No command provided"
    show_usage
    exit 1
fi

# Execute commands
case $COMMAND in
    init)
        print_info "Creating initial migrations..."
        run_migration_script init
        ;;
    
    setup)
        print_info "Setting up database schema..."
        run_migration_script setup
        ;;
    
    create)
        if [[ -z "$MESSAGE" ]]; then
            print_error "Migration message is required for create command"
            exit 1
        fi
        print_info "Creating migration: $MESSAGE"
        if [[ "$DB_TYPE" == "tenant" ]]; then
            run_migration_script create "$MESSAGE" --type tenant
        else
            run_migration_script create "$MESSAGE" --type master
        fi
        ;;
    
    upgrade)
        case $DB_TYPE in
            master)
                print_info "Upgrading master database..."
                if [[ -n "$REVISION" ]]; then
                    run_migration_script upgrade --type master --revision "$REVISION"
                else
                    run_migration_script upgrade --type master
                fi
                ;;
            tenant)
                if [[ -z "$TENANT_ID" ]]; then
                    print_error "Tenant ID is required for tenant upgrade"
                    exit 1
                fi
                print_info "Upgrading tenant $TENANT_ID database..."
                if [[ -n "$REVISION" ]]; then
                    run_migration_script upgrade --type tenant --tenant-id "$TENANT_ID" --revision "$REVISION"
                else
                    run_migration_script upgrade --type tenant --tenant-id "$TENANT_ID"
                fi
                ;;
            all)
                print_info "Upgrading all tenant databases..."
                if [[ -n "$REVISION" ]]; then
                    run_migration_script upgrade --type all --revision "$REVISION"
                else
                    run_migration_script upgrade --type all
                fi
                ;;
        esac
        ;;
    
    downgrade)
        case $DB_TYPE in
            master)
                print_info "Downgrading master database..."
                if [[ -n "$REVISION" ]]; then
                    run_migration_script downgrade --type master --revision "$REVISION"
                else
                    run_migration_script downgrade --type master
                fi
                ;;
            tenant)
                if [[ -z "$TENANT_ID" ]]; then
                    print_error "Tenant ID is required for tenant downgrade"
                    exit 1
                fi
                print_info "Downgrading tenant $TENANT_ID database..."
                if [[ -n "$REVISION" ]]; then
                    run_migration_script downgrade --type tenant --tenant-id "$TENANT_ID" --revision "$REVISION"
                else
                    run_migration_script downgrade --type tenant --tenant-id "$TENANT_ID"
                fi
                ;;
        esac
        ;;
    
    current)
        case $DB_TYPE in
            master)
                print_info "Showing current master database revision..."
                run_migration_script current --type master
                ;;
            tenant)
                if [[ -z "$TENANT_ID" ]]; then
                    print_error "Tenant ID is required for tenant current"
                    exit 1
                fi
                print_info "Showing current tenant $TENANT_ID database revision..."
                run_migration_script current --type tenant --tenant-id "$TENANT_ID"
                ;;
        esac
        ;;
    
    history)
        case $DB_TYPE in
            master)
                print_info "Showing master database migration history..."
                run_migration_script history --type master
                ;;
            tenant)
                if [[ -z "$TENANT_ID" ]]; then
                    print_error "Tenant ID is required for tenant history"
                    exit 1
                fi
                print_info "Showing tenant $TENANT_ID database migration history..."
                run_migration_script history --type tenant --tenant-id "$TENANT_ID"
                ;;
        esac
        ;;
    
    status)
        print_info "Showing database status..."
        echo ""
        echo "=== Master Database ==="
        run_migration_script current --type master
        echo ""
        echo "=== Tenant Databases ==="
        # This would require additional logic to iterate through all tenants
        print_warning "Tenant status check not implemented yet. Use 'current --tenant <id>' for specific tenants."
        ;;
    
    *)
        print_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac

print_success "Operation completed!"