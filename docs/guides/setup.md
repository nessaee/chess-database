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
- [ ] Ports 5173, 5000, and 5432 available

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
POSTGRES_DB=chess-test
POSTGRES_PORT=5432
```

```bash
# src/.env.backend
DATABASE_URL=postgresql+asyncpg://postgres:chesspass@db:5432/chess-test
API_BASE_URL=http://localhost:5000
DB_HOST=db
CACHE_TTL=3600
LOG_FILE=app.log
LOG_LEVEL=INFO
RATE_LIMIT=100
```

> ⚠️ **Note**: Never commit these .env files to version control. Add them to your .gitignore file.

### 3. Initialize Docker Environment
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

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
The database configuration is stored in `.env.db`:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=chesspass
POSTGRES_DB=chess-test
POSTGRES_PORT=5432
```

### Backend Settings
The backend configuration is stored in `.env.backend`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:chesspass@db:5432/chess-test
API_BASE_URL=http://localhost:5000
DB_HOST=db
CACHE_TTL=3600
LOG_FILE=app.log
LOG_LEVEL=INFO
RATE_LIMIT=100
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
cp .env.backend .env.backend.prod
cp .env.db .env.db.prod
```

Edit the production environment files with appropriate values for your production environment.

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
docker-compose exec db psql -U postgres -d chess-test
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

## Next Steps
- [Development Guide](development.md)
- [API Documentation](../backend/api.md)
- [Frontend Guide](../frontend/components.md)
- [Deployment Guide](deployment.md)
