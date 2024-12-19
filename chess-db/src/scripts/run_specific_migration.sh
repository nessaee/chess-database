#!/bin/bash

# Check if migration version is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <migration_version>"
    echo "Example: $0 v_0.0.7"
    exit 1
fi

# Get migration version from argument
MIGRATION_VERSION=$1

# Change to the root directory of the project
cd "$(dirname "$0")/.." || exit 1

# Source environment variables
if [ ! -f ".env.db" ]; then
    echo "Error: .env.db file not found in project root"
    exit 1
fi
source .env.db

# Find migration file
MIGRATION_FILE=$(find backend/migrations -name "${MIGRATION_VERSION}*.sql" | head -n 1)
if [ -z "$MIGRATION_FILE" ]; then
    echo "Error: Migration file not found for version ${MIGRATION_VERSION}"
    exit 1
fi

# Check if containers are running
if ! docker ps | grep -q src-db-1; then
    echo "Starting containers..."
    docker compose up -d db
    
    # Wait for database to be ready
    echo "Waiting for database to be ready..."
    sleep 5
    until docker exec src-db-1 pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
        echo "Database is not ready - waiting..."
        sleep 2
    done
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Applying migration: ${MIGRATION_VERSION}"

# Copy migration file into container
MIGRATION_FILENAME=$(basename "$MIGRATION_FILE")
echo "Copying migration file into container..."
if ! docker cp "$MIGRATION_FILE" "src-db-1:/tmp/$MIGRATION_FILENAME"; then
    echo "Error: Failed to copy migration file into container"
    exit 1
fi

# Execute the migration
docker exec src-db-1 psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "/tmp/$MIGRATION_FILENAME"
MIGRATION_STATUS=$?

# Clean up the temporary file
docker exec src-db-1 rm -f "/tmp/$MIGRATION_FILENAME"

if [ $MIGRATION_STATUS -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Successfully applied migration: ${MIGRATION_VERSION}"
    
    # Update schema_migrations table
    docker exec src-db-1 psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
        "INSERT INTO schema_migrations (version) VALUES ('${MIGRATION_VERSION}') ON CONFLICT (version) DO NOTHING;"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Failed to apply migration: ${MIGRATION_VERSION}"
    exit 1
fi
