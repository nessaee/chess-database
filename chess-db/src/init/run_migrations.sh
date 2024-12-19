#!/bin/bash
# run_migrations.sh - Database Migration Script
# Purpose: Apply SQL migrations to the chess database
# Usage: ./run_migrations.sh [--check-only]

# Exit on any error
set -e

# Source environment files
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_DB="${PROJECT_ROOT}/.env.db"
ENV_BACKEND="${PROJECT_ROOT}/.env.backend"
MIGRATIONS_DIR="${PROJECT_ROOT}/backend/migrations"

# Load environment variables
if [ -f "$ENV_DB" ] && [ -f "$ENV_BACKEND" ]; then
    set -a  # automatically export all variables
    source "$ENV_DB"
    source "$ENV_BACKEND"
    set +a
else
    echo "Error: Environment files not found. Please ensure .env.db and .env.backend exist"
    exit 1
fi

# Color coding for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log() { echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }
error() { log "${RED}ERROR: $1${NC}"; }
success() { log "${GREEN}SUCCESS: $1${NC}"; }
warning() { log "${YELLOW}WARNING: $1${NC}"; }

# Function to check if database is ready
check_db() {
    log "Checking database connection..."
    
    max_attempts=30
    counter=0
    
    while [ $counter -lt $max_attempts ]; do
        if docker compose exec -T db pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" > /dev/null 2>&1; then
            success "Database is ready"
            return 0
        fi
        
        counter=$((counter + 1))
        log "Waiting for database to be ready... ($counter/$max_attempts)"
        sleep 2
    done
    
    error "Database not ready after $max_attempts attempts"
    return 1
}

# Function to run migrations
run_migrations() {
    local check_only=$1
    
    if [ ! -d "$MIGRATIONS_DIR" ]; then
        warning "No migrations directory found at ${MIGRATIONS_DIR}"
        return 0
    fi
    
    log "Applying migrations from ${MIGRATIONS_DIR}..."
    
    # Create migrations table if it doesn't exist
    docker compose exec -T db psql -U "${POSTGRES_USER}" "${POSTGRES_DB}" <<-EOSQL
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
EOSQL
    
    # Get list of applied migrations
    applied_migrations=$(docker compose exec -T db psql -U "${POSTGRES_USER}" "${POSTGRES_DB}" -t -c "SELECT version FROM schema_migrations ORDER BY version;")
    
    # Count pending migrations
    pending_count=0
    for migration in $(ls -v "${MIGRATIONS_DIR}"/v_*.sql); do
        version=$(basename "$migration" .sql)
        if ! echo "$applied_migrations" | grep -q "$version"; then
            pending_count=$((pending_count + 1))
        fi
    done
    
    if [ $pending_count -eq 0 ]; then
        success "No pending migrations"
        return 0
    fi
    
    log "Found $pending_count pending migration(s)"
    
    if [ "$check_only" = true ]; then
        warning "Check-only mode: skipping migration application"
        return 0
    fi
    
    # Apply each migration in order
    for migration in $(ls -v "${MIGRATIONS_DIR}"/v_*.sql); do
        version=$(basename "$migration" .sql)
        
        # Check if migration was already applied
        if ! echo "$applied_migrations" | grep -q "$version"; then
            log "Applying migration: $version"
            
            # Apply the migration
            if docker compose exec -T db psql -U "${POSTGRES_USER}" "${POSTGRES_DB}" < "$migration"; then
                # Record successful migration
                docker compose exec -T db psql -U "${POSTGRES_USER}" "${POSTGRES_DB}" <<-EOSQL
                    INSERT INTO schema_migrations (version) VALUES ('$version');
EOSQL
                log "Successfully applied migration: $version"
            else
                error "Failed to apply migration: $version"
                exit 1
            fi
        else
            log "Skipping already applied migration: $version"
        fi
    done
    
    success "Migrations completed successfully"
}

# Parse command line arguments
check_only=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --check-only)
            check_only=true
            shift
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Main execution
check_db
run_migrations "$check_only"
