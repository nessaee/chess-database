# Chess Database Setup Guide

This guide explains how to set up the chess database system from scratch using a backup file.

## Prerequisites

- Docker installed and running
- PostgreSQL client (psql) installed
- Python 3 installed
- A database backup file (`.gz` format)

## Quick Start

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd chess-db
   ```

2. Make the setup script executable:
   ```bash
   chmod +x src/init/setup_chess_db.sh
   ```

3. Run the setup script with your backup file:
   ```bash
   ./src/init/setup_chess_db.sh path/to/your/backup.gz
   ```

## What the Setup Does

The setup process:

1. **Checks Prerequisites**
   - Verifies all required tools are installed
   - Validates the backup file exists

2. **Database Initialization**
   - Creates a PostgreSQL container if not exists
   - Sets up the database environment
   - Default configuration:
     - Database: chess
     - User: postgres
     - Password: chesspass
     - Port: 5433
     - Host: localhost

3. **Data Restoration**
   - Restores data from the provided backup file
   - Handles compression automatically

4. **Migrations**
   - Runs all necessary database migrations in the correct order
   - Creates required views and indexes
   - Sets up performance monitoring

## Configuration

The default configuration can be modified by editing the variables at the top of `src/init/setup_chess_db.sh`:

```bash
DB_NAME="chess"
DB_USER="postgres"
DB_PASSWORD="chesspass"
DB_PORT="5433"
DB_HOST="localhost"
CONTAINER_NAME="src-db-1"
```

## Safety Features

The setup script includes several safety measures:

- Checks for existing databases before proceeding
- Prompts for confirmation before dropping existing databases
- Validates all prerequisites before starting
- Provides clear error messages and logging
- Rolls back changes if any step fails

## Troubleshooting

1. **Docker Issues**
   ```
   ERROR: Docker is not running
   ```
   Solution: Start Docker service
   ```bash
   sudo systemctl start docker
   ```

2. **Permission Issues**
   ```
   ERROR: Permission denied
   ```
   Solution: Run with appropriate permissions
   ```bash
   sudo chmod +x src/init/setup_chess_db.sh
   ```

3. **Database Connection Issues**
   ```
   ERROR: Failed to connect to database
   ```
   Solution: Check if PostgreSQL container is running
   ```bash
   docker ps
   ```

## Migration Details

The migrations are run in the following order:

1. Move count statistics view
2. Game opening matches view
3. Player opening statistics view

Each migration checks its dependencies before running.

## Backup and Restore

To create a new backup:
```bash
pg_dump -h localhost -p 5433 -U postgres chess | gzip > chess_backup_$(date +%Y%m%d).gz
```

To restore from a backup manually:
```bash
gunzip -c backup_file.gz | psql -h localhost -p 5433 -U postgres chess
```

## Contributing

Please read our contributing guidelines before submitting pull requests.

## License

[Your License Information]
