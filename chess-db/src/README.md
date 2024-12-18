# Chess Database Setup Guide

## Table of Contents

- [Chess Database Setup Guide](#chess-database-setup-guide)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Prerequisites](#prerequisites)
  - [Step-by-Step Setup](#step-by-step-setup)
    - [1. Clone the Repository](#1-clone-the-repository)
    - [2. Environment Setup](#2-environment-setup)
    - [3. Initialize Docker Environment](#3-initialize-docker-environment)
    - [4. Verify Services](#4-verify-services)
  - [Directory Structure](#directory-structure)
  - [Configuration Options](#configuration-options)
    - [Database Settings](#database-settings)
    - [Frontend Settings](#frontend-settings)
    - [Backend Settings](#backend-settings)
  - [Development Workflow](#development-workflow)
    - [Starting the Environment](#starting-the-environment)
    - [Viewing Logs](#viewing-logs)
    - [Making Changes](#making-changes)
    - [Stopping the Environment](#stopping-the-environment)
  - [Backup and Recovery](#backup-and-recovery)
    - [Creating Backups](#creating-backups)
    - [Restoring Backups](#restoring-backups)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
    - [Health Checks](#health-checks)
  - [Security Notes](#security-notes)
  - [Production Deployment](#production-deployment)
  - [Support](#support)

## Overview

This guide provides step-by-step instructions for setting up the chess database system, which consists of:

1. **Frontend**: React application for chess game analysis
2. **Backend**: FastAPI server handling game processing and database operations
3. **Database**: PostgreSQL database storing chess games and analysis

## Prerequisites

Before starting, ensure you have:

- [ ] Docker Engine (20.10.0 or higher)
- [ ] Docker Compose (v2.0.0 or higher)
- [ ] Git
- [ ] At least 4GB of free disk space
- [ ] Ports 5173, 5000, and 5433 available

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo/chess-db.git
cd chess-db
```

### 2. Environment Setup

**UPDATE THIS**

Create two environment files in the `src` directory:

```bash
# src/.env.db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=chesspass
POSTGRES_DB=chess
```

```bash
# src/.env.backend
DATABASE_URL=postgresql+asyncpg://postgres:chesspass@db:5432/chess
```

These environment files are used by Docker Compose to configure the services:
- `.env.db` configures the PostgreSQL database service
- `.env.backend` configures the FastAPI backend service

The environment files should be placed in the same directory as your `docker-compose.yml` file (the `src` directory).

> ⚠️ **Note**: Never commit these .env files to version control. Add them to your .gitignore file.

### 3. Initialize Docker Environment

```bash
cd src/init
chmod +x docker_init.sh
./docker_init.sh path/to/backup.gz
```

This script will:
- Check prerequisites
- Clean up existing containers
- Build and start containers
- Initialize the database
- Restore from backup (if provided)
- Run migrations
- Verify the setup

### 4. Verify Services

After setup, verify these endpoints:

- Frontend: http://localhost:5173
  - Should show the chess analysis interface
- Backend: http://localhost:5000/docs
  - Should show the FastAPI documentation
- Database: Port 5433
  - Test connection: `psql -h localhost -p 5433 -U postgres -d chess`

## Directory Structure

```
chess-db/
├── src/
│   ├── frontend/          # React frontend
│   ├── backend/           # FastAPI backend
│   ├── init/             # Setup scripts
│   │   ├── docker_init.sh
│   │   └── setup_chess_db.sh
│   └── docker-compose.yml
├── migrations/           # Database migrations
└── docs/                # Additional documentation
```

## Configuration Options

### Database Settings

The database configuration is managed through environment files in the root directory. All variables are required:

1. `.env.db` - Core database settings:
   ```bash
   # Required Database Settings
   POSTGRES_DB=chess           # Database name
   POSTGRES_USER=postgres      # Database user
   POSTGRES_PASSWORD=chesspass # Database password
   POSTGRES_PORT=5433         # Database port
   POSTGRES_CONTAINER_NAME=src-db-1  # Docker container name
   ```

2. `.env.backend` - Backend-specific settings:
   ```bash
   # Required Database Settings
   DB_HOST=localhost          # Database host
   TEST_DB_NAME=chess-test   # Test database name

   # Required API Settings
   API_BASE_URL=http://localhost:5000  # Base URL for API

   # Required Cache Settings
   CACHE_TTL=300             # Cache time-to-live in seconds

   # Required Logging Settings
   LOG_FILE=api.log          # Log file path
   LOG_LEVEL=INFO           # Logging level (DEBUG, INFO, WARNING, ERROR)

   # Required Rate Limiting
   RATE_LIMIT=100/minute    # API rate limit
   ```

All initialization scripts and backend services require these environment files. To set up:

1. Copy the example environment files:
   ```bash
   cp .env.db.example .env.db
   cp .env.backend.example .env.backend
   ```

2. Edit both files with your configuration. These settings are used by:
   - Database initialization scripts
   - Backend FastAPI service
   - Database container configuration
   - Test environment setup

The application will fail to start if any required environment variables are missing.

### Frontend Settings

- Port: 5173
- Environment variables:
  - `VITE_API_URL`: Backend API URL
  - `VITE_WS_URL`: WebSocket URL (if used)

### Backend Settings

- Port: 5000 (host) → 8000 (container)
- Environment variables:
  - `DATABASE_URL`: PostgreSQL connection string
  - `DEBUG`: Enable debug mode (true/false)

## Development Workflow

### Starting the Environment

```bash
cd src
docker-compose up -d
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f [frontend|backend|db]
```

### Making Changes

1. Frontend changes:
   - Edit files in `frontend/src/`
   - Changes hot-reload automatically

2. Backend changes:
   - Edit files in `backend/`
   - Changes hot-reload automatically

3. Database changes:
   - Create migration in `migrations/`
   - Apply: `docker-compose exec backend python migrations/run_migrations.py`

### Stopping the Environment

```bash
docker-compose down
```

## Backup and Recovery

### Creating Backups

```bash
# Full database backup
./scripts/backup.sh

# Specific tables
docker-compose exec db pg_dump -U postgres -t table_name chess > backup_table.sql
```

### Restoring Backups

```bash
# Full restore
./scripts/restore.sh backup_file.gz

# Specific tables
cat backup_table.sql | docker-compose exec -T db psql -U postgres chess
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check ports
   sudo lsof -i :5173
   sudo lsof -i :5000
   sudo lsof -i :5433
   ```

2. **Database Connection Failed**
   ```bash
   # Check database status
   docker-compose ps db
   docker-compose logs db
   ```

3. **Permission Issues**
   ```bash
   # Fix volume permissions
   sudo chown -R $USER:$USER .
   ```

### Health Checks

```bash
# Check all services
docker-compose ps

# Test database connection
docker-compose exec db pg_isready -U postgres

# Test backend health
curl http://localhost:5000/health
```

## Security Notes

- Change default passwords in production
- Use `.env` files for sensitive data
- Keep backups secure and encrypted
- Regularly update dependencies
- Monitor container logs for suspicious activity

## Production Deployment

Additional steps for production:

1. Use proper SSL/TLS certificates
2. Set up proper authentication
3. Configure backup automation
4. Set up monitoring and alerts
5. Use production-grade database settings

## Support

For issues:
1. Check troubleshooting guide
2. Review logs
3. Create GitHub issue with:
   - Error messages
   - Environment details
   - Steps to reproduce
