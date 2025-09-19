#!/bin/bash

# Docker migration script for multi-tenant invoice application
# This script runs migrations inside Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed or not in PATH"
    exit 1
fi

# Get the project root directory (assuming this script is in api/scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Function to run migration command in Docker
run_docker_migration() {
    local cmd="$1"
    shift
    
    print_info "Running migration command in Docker: $cmd $*"
    
    cd "$PROJECT_ROOT"
    
    # Check if API container is running
    if ! docker-compose ps api | grep -q "Up"; then
        print_error "API container is not running. Please start it with: docker-compose up -d api"
        exit 1
    fi
    
    # Run the migration command
    docker-compose exec api python scripts/manage_migrations.py "$cmd" "$@"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "This script runs database migrations inside Docker containers."
    echo "Make sure your Docker services are running before using this script."
    echo ""
    echo "Commands:"
    echo "  init                     Create initial migrations"
    echo "  setup                    Set up database schema"
    echo "  create <message>         Create a new migration"
    echo "    --master               Create migration for master database (default)"
    echo "    --tenant               Create migration for tenant database"
    echo "  upgrade                  Upgrade database"
    echo "    --master               Upgrade master database (default)"
    echo "    --tenant <id>          Upgrade specific tenant database"
    echo "    --all-tenants          Upgrade all tenant databases"
    echo "  current                  Show current database revision"
    echo "    --master               Show master database revision (default)"
    echo "    --tenant <id>          Show specific tenant database revision"
    echo ""
    echo "Examples:"
    echo "  $0 init                                    # Create initial migrations"
    echo "  $0 setup                                   # Set up database schema"
    echo "  $0 create \"Add user table\" --master        # Create master DB migration"
    echo "  $0 upgrade --all-tenants                   # Upgrade all tenant databases"
    echo ""
    echo "Prerequisites:"
    echo "  - Docker and docker-compose must be installed"
    echo "  - Run 'docker-compose up -d' to start services first"
}

# Parse command line arguments
COMMAND=""
DB_TYPE="master"
TENANT_ID=""
MESSAGE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        init|setup|create|upgrade|current)
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
        run_docker_migration init
        ;;
    
    setup)
        run_docker_migration setup
        ;;
    
    create)
        if [[ -z "$MESSAGE" ]]; then
            print_error "Migration message is required for create command"
            exit 1
        fi
        if [[ "$DB_TYPE" == "tenant" ]]; then
            run_docker_migration create "$MESSAGE" --type tenant
        else
            run_docker_migration create "$MESSAGE" --type master
        fi
        ;;
    
    upgrade)
        case $DB_TYPE in
            master)
                run_docker_migration upgrade --type master
                ;;
            tenant)
                if [[ -z "$TENANT_ID" ]]; then
                    print_error "Tenant ID is required for tenant upgrade"
                    exit 1
                fi
                run_docker_migration upgrade --type tenant --tenant-id "$TENANT_ID"
                ;;
            all)
                run_docker_migration upgrade --type all
                ;;
        esac
        ;;
    
    current)
        case $DB_TYPE in
            master)
                run_docker_migration current --type master
                ;;
            tenant)
                if [[ -z "$TENANT_ID" ]]; then
                    print_error "Tenant ID is required for tenant current"
                    exit 1
                fi
                run_docker_migration current --type tenant --tenant-id "$TENANT_ID"
                ;;
        esac
        ;;
    
    *)
        print_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac

print_success "Docker migration operation completed!"