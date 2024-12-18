#!/bin/bash
# setup.sh - Chess Database Setup Script
# Purpose: Set up PostgreSQL database, restore from backup, and run migrations
# Usage: ./setup.sh <backup_file.gz>

# Exit on any error
set -e

# Configuration variables
DB_NAME="chess"
DB_USER="postgres"
DB_PASSWORD="chesspass"
DB_PORT="5433"
DB_HOST="localhost"
CONTAINER_NAME="src-db-1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATIONS_DIR="${SCRIPT_DIR}/../backend/migrations"

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
    }
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker is not running"
        exit 1
    }
    
    # Check if psql is installed
    if ! command -v psql &> /dev/null; then
        error "PostgreSQL client (psql) is not installed"
        exit 1
    }
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
        exit 1
    }
    
    success "All prerequisites met"
}

# Function to check if database exists
check_existing_db() {
    log "Checking for existing database..."
    if docker exec $CONTAINER_NAME psql -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
        warning "Database '$DB_NAME' already exists!"
        read -p "Do you want to drop and recreate it? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Setup aborted by user"
            exit 1
        fi
    fi
}

# Function to initialize database
init_database() {
    log "Initializing database environment..."
    
    # Source the init_db.sh script
    if [ -f "${SCRIPT_DIR}/init_db.sh" ]; then
        source "${SCRIPT_DIR}/init_db.sh"
    else
        error "init_db.sh not found in ${SCRIPT_DIR}"
        exit 1
    fi
}

# Function to restore from backup
restore_backup() {
    local backup_file=$1
    log "Restoring database from backup: $backup_file"
    
    # Drop database if it exists
    docker exec $CONTAINER_NAME psql -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;"
    docker exec $CONTAINER_NAME psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;"
    
    # Restore from backup
    gunzip -c "$backup_file" | docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME
    
    success "Database restored successfully"
}

# Function to run migrations
run_migrations() {
    log "Running database migrations..."
    
    # Check if migrations directory exists
    if [ ! -d "$MIGRATIONS_DIR" ]; then
        error "Migrations directory not found: $MIGRATIONS_DIR"
        exit 1
    }
    
    # Run the Python migration script
    python3 "${MIGRATIONS_DIR}/run_migrations.py"
    
    success "Migrations completed successfully"
}

# Function to verify setup
verify_setup() {
    log "Verifying database setup..."
    
    # Test database connection
    if docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c '\dt' > /dev/null 2>&1; then
        success "Database connection verified"
    else
        error "Failed to connect to database"
        exit 1
    fi
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
    echo "psql -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME"
}

# Execute main function
main "$@"
