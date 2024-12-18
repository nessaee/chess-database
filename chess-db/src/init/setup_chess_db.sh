#!/bin/bash
# setup_chess_db.sh - Complete Chess Database Setup Script
# Purpose: Set up PostgreSQL database, restore from backup, and run migrations
# Usage: ./setup_chess_db.sh <backup_file.gz>

# Exit on any error
set -e

# Source environment files
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_DB="${PROJECT_ROOT}/.env.db"
ENV_BACKEND="${PROJECT_ROOT}/.env.backend"
MIGRATIONS_DIR="${PROJECT_ROOT}/backend/migrations"

# Check if environment files exist
if [ ! -f "$ENV_DB" ] || [ ! -f "$ENV_BACKEND" ]; then
    error "Environment files not found. Please ensure .env.db and .env.backend exist"
    exit 1
fi

# Load environment variables
set -a  # automatically export all variables
source "$ENV_DB"
source "$ENV_BACKEND"
set +a

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

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if backup file exists
    if [ -z "$1" ]; then
        error "No backup file specified. Usage: $0 <backup_file.gz>"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        error "Backup file '$1' not found"
        exit 1
    fi
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker is not running"
        exit 1
    fi
    
    # Check if psql is installed
    if ! command -v psql &> /dev/null; then
        error "PostgreSQL client (psql) is not installed"
        exit 1
    fi
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
        exit 1
    fi
    
    success "All prerequisites met"
}

# Function to check if database exists
check_existing_db() {
    log "Checking if database exists..."
    
    if docker compose exec db psql -U "${POSTGRES_USER}" -lqt | cut -d \| -f 1 | grep -qw "${POSTGRES_DB}"; then
        warning "Database '${POSTGRES_DB}' already exists"
        read -p "Do you want to drop and recreate it? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Setup aborted"
            exit 1
        fi
    fi
}

# Function to initialize database
init_database() {
    log "Initializing database..."
    
    docker compose exec db dropdb -U "${POSTGRES_USER}" --if-exists "${POSTGRES_DB}"
    docker compose exec db createdb -U "${POSTGRES_USER}" "${POSTGRES_DB}"
    
    success "Database initialized"
}

# Function to restore from backup
restore_backup() {
    local backup_file=$1
    log "Restoring from backup: $backup_file"
    
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        exit 1
    fi
    
    gunzip -c "$backup_file" | docker compose exec -T db psql -U "${POSTGRES_USER}" "${POSTGRES_DB}"
    
    success "Backup restored successfully"
}

# Function to run migrations
run_migrations() {
    log "Running database migrations..."
    
    if [ -d "$MIGRATIONS_DIR" ]; then
        log "Applying migrations from ${MIGRATIONS_DIR}..."
        docker compose exec web alembic upgrade head
        success "Migrations completed successfully"
    else
        warning "No migrations directory found at ${MIGRATIONS_DIR}"
    fi
}

# Function to verify setup
verify_setup() {
    log "Verifying database setup..."
    
    if ! docker compose exec db pg_isready -U "${POSTGRES_USER}" > /dev/null 2>&1; then
        error "Database is not responding"
        exit 1
    fi
    
    if ! docker compose exec db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c '\dt' > /dev/null 2>&1; then
        error "Cannot connect to database"
        exit 1
    fi
    
    success "Database setup verified"
}

# Main execution
main() {
    local backup_file=$1
    
    echo "Chess Database Setup"
    echo "==================="
    
    # Run all setup steps
    check_prerequisites "$backup_file"
    check_existing_db
    init_database
    restore_backup "$backup_file"
    run_migrations
    verify_setup
    
    success "Database setup completed successfully!"
    echo
    echo "You can now connect to the database using:"
    echo "psql -h localhost -p ${POSTGRES_PORT} -U ${POSTGRES_USER} ${POSTGRES_DB}"
}

# Execute main function
main "$@"
