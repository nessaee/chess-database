#!/bin/bash
# db_init.sh - Database Initialization and Verification Script
# Purpose: Initialize PostgreSQL database and verify its proper operation
# Usage: ./db_init.sh

# Exit on any error
set -e

# Configuration variables
DB_NAME="chess"
DB_USER="postgres"
DB_PASSWORD="chesspass"
DB_PORT="5433"
DB_HOST="localhost"
CONTAINER_NAME="src-db-1"

# Color coding for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function with timestamp
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    log "${RED}ERROR: $1${NC}"
}

success() {
    log "${GREEN}SUCCESS: $1${NC}"
}

warning() {
    log "${YELLOW}WARNING: $1${NC}"
}

# Function to check if Docker is running
check_docker() {
    log "Checking Docker service..."
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running or not accessible"
        exit 1
    fi
    success "Docker is running"
}

# Function to clean up existing PostgreSQL container and volume
cleanup_existing() {
    log "Cleaning up existing PostgreSQL container and volume..."
    
    # Stop existing container if running
    if docker ps -q -f name="$CONTAINER_NAME" >/dev/null; then
        warning "Stopping existing PostgreSQL container..."
        docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    fi
    
    # Remove container
    if docker ps -aq -f name="$CONTAINER_NAME" >/dev/null; then
        warning "Removing existing PostgreSQL container..."
        docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
    fi
    
    # Remove volume
    if docker volume ls -q -f name="postgres_data" >/dev/null; then
        warning "Removing existing PostgreSQL volume..."
        docker volume rm postgres_data >/dev/null 2>&1 || true
    fi
    
    success "Cleanup completed"
}

# Function to start PostgreSQL
start_postgres() {
    log "Starting PostgreSQL container..."
    docker compose up -d db
    
    # Wait for container to be ready
    local retries=0
    local max_retries=30
    
    while [ $retries -lt $max_retries ]; do
        if docker compose logs db | grep -q "database system is ready to accept connections"; then
            success "PostgreSQL is ready"
            return 0
        fi
        warning "Waiting for PostgreSQL to be ready... ($(( retries + 1 ))/$max_retries)"
        sleep 2
        (( retries++ ))
    done
    
    error "PostgreSQL failed to start within the expected time"
    return 1
}

# Function to verify database connection
verify_connection() {
    log "Verifying database connection..."
    local retries=0
    local max_retries=5
    
    while [ $retries -lt $max_retries ]; do
        if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c '\conninfo' >/dev/null 2>&1; then
            success "Successfully connected to database"
            return 0
        fi
        warning "Connection attempt failed... ($(( retries + 1 ))/$max_retries)"
        sleep 2
        (( retries++ ))
    done
    
    error "Failed to verify database connection"
    return 1
}

# Main execution
main() {
    log "Starting database initialization process"
    
    check_docker
    cleanup_existing
    start_postgres
    verify_connection
    
    success "Database initialization completed successfully"
}

# Execute main function
main "$@"