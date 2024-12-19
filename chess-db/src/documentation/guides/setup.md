# Setup Guide

[← Documentation Home](../index.md) | [Development Guide](development.md) | [Deployment Guide](deployment.md)

**Path**: documentation/guides/setup.md

## Navigation
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Development Setup](#development-setup)
- [Production Setup](#production-setup)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before starting, ensure you have:

- [ ] Docker Engine (20.10.0 or higher)
- [ ] Docker Compose (v2.0.0 or higher)
- [ ] Git
- [ ] At least 4GB of free disk space
- [ ] Ports 5173, 5000, and 5433 available

### Development Tools (Optional)
- Visual Studio Code (recommended)
- pgAdmin or DBeaver
- Postman

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/your-repo/chess-db.git
cd chess-db
```

### 2. Environment Setup
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

### 4. Verify Services
After initialization, verify that all services are running:

```bash
docker-compose ps
```

Expected output:
```
NAME                COMMAND                  SERVICE             STATUS
chess-db-api        "uvicorn main:app --…"   api                running
chess-db-db         "docker-entrypoint.s…"   db                 running
chess-db-frontend   "npm run dev"            frontend           running
```

## Configuration

### Database Settings
```env
# src/.env.db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=chesspass
POSTGRES_DB=chess
POSTGRES_PORT=5433
```

### Backend Settings
```env
# src/.env.backend
DATABASE_URL=postgresql+asyncpg://postgres:chesspass@db:5432/chess
API_HOST=0.0.0.0
API_PORT=5000
DEBUG=True
```

### Frontend Settings
```env
# src/.env.frontend
VITE_API_URL=http://localhost:5000
VITE_WS_URL=ws://localhost:5000/ws
```

## Development Setup

### Start Development Environment
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Making Changes
1. Frontend changes (hot-reload enabled):
   - Edit files in `src/frontend/`
   - Changes apply automatically

2. Backend changes:
   - Edit files in `src/backend/`
   - API will reload automatically

3. Database changes:
   - Create migration: `alembic revision -m "description"`
   - Apply migration: `alembic upgrade head`

### Stop Environment
```bash
docker-compose down
```

## Production Setup

### 1. Build Production Images
```bash
docker-compose -f docker-compose.prod.yml build
```

### 2. Configure Production Environment
Copy and edit production environment files:
```bash
cp .env.prod.example .env.prod
cp .env.db.prod.example .env.db.prod
```

### 3. Deploy Services
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database logs
docker-compose logs db

# Verify connection
docker-compose exec db psql -U postgres -d chess
```

#### Service Health Checks
```bash
# Backend health
curl http://localhost:5000/health

# Database health
docker-compose exec db pg_isready

# View all logs
docker-compose logs -f
```

### Backup and Recovery

#### Create Backup
```bash
./scripts/backup.sh
```

#### Restore from Backup
```bash
./scripts/restore.sh path/to/backup.gz
```

## Next Steps
- [Development Guide](development.md)
- [API Documentation](../design/backend/api.md)
- [Frontend Guide](../design/frontend/components.md)
- [Deployment Guide](deployment.md)
