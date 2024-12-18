#!/bin/bash
# docker_init.sh - Docker Environment Setup Script
# Purpose: Initialize and configure Docker environment for chess database
# Usage: ./docker_init.sh <backup_file.gz>

# Exit on any error
set -e

# Source environment files
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_DB="${PROJECT_ROOT}/.env.db"
ENV_BACKEND="${PROJECT_ROOT}/.env.backend"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
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
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker is not running"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    success "All prerequisites met"
}

# Function to check ports
check_ports() {
    local web_port="${WEB_PORT:-5173}"
    local api_port="${API_PORT:-5000}"
    local db_port="${POSTGRES_PORT:-5433}"
    local ports=($web_port $api_port $db_port)
    
    for port in "${ports[@]}"; do
        if lsof -i:$port > /dev/null 2>&1; then
            error "Port $port is already in use"
            exit 1
        fi
    done
    success "All required ports are available"
}

# Function to clean up existing containers
cleanup_existing() {
    log "Cleaning up existing containers..."
    
    cd "$PROJECT_ROOT"
    if [ -f "$COMPOSE_FILE" ]; then
        docker compose down -v
    fi
    
    success "Cleanup completed"
}

# Function to build and start containers
start_containers() {
    log "Starting Docker containers..."
    
    cd "$PROJECT_ROOT"
    docker compose build --no-cache
    docker compose up -d
    
    success "Containers started successfully"
}

# Function to wait for database
wait_for_db() {
    log "Waiting for database to be ready..."
    
    local retries="${DB_INIT_TIMEOUT:-30}"
    local interval=2
    
    while [ $retries -gt 0 ]; do
        if docker compose exec db pg_isready -U "${POSTGRES_USER}" > /dev/null 2>&1; then
            success "Database is ready"
            return 0
        fi
        retries=$((retries-1))
        sleep $interval
    done
    
    error "Database failed to become ready"
    exit 1
}

# Function to restore database
restore_database() {
    local backup_file=$1
    log "Restoring database from backup: $backup_file"
    
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        exit 1
    fi
    
    cd "$PROJECT_ROOT"
    gunzip -c "$backup_file" | docker compose exec -T db psql -U "${POSTGRES_USER}" "${POSTGRES_DB}"
    
    success "Database restored successfully"
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
    log "Verifying setup..."
    
    # Check if all containers are running
    cd "$PROJECT_ROOT"
    local running_containers=$(docker compose ps --services --filter "status=running" | wc -l)
    if [ "$running_containers" -ne 3 ]; then
        error "Not all containers are running"
        docker compose ps
        exit 1
    fi
    
    # Test database connection
    if ! docker compose exec db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c '\dt' > /dev/null 2>&1; then
        error "Could not connect to database"
        exit 1
    fi
    
    success "Setup verified successfully"
}

# Main execution
main() {
    local backup_file=$1
    
    echo "Chess Database Docker Setup"
    echo "=========================="
    
    # Run all setup steps
    check_prerequisites
    check_ports
    cleanup_existing
    start_containers
    wait_for_db
    
    if [ -n "$backup_file" ]; then
        restore_database "$backup_file"
        run_migrations
    fi
    
    verify_setup
    
    success "Docker environment setup completed successfully!"
    echo
    echo "Services are available at:"
    echo "- Frontend: http://localhost:${WEB_PORT:-5173}"
    echo "- Backend:  http://localhost:${API_PORT:-5000}"
    echo "- Database: postgresql://localhost:${POSTGRES_PORT:-5433}"
}

# Execute main function
main "$@"
