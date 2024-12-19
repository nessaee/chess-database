# Deployment Guide

## Prerequisites
- Docker
- PostgreSQL 13+
- Python 3.9+

## Environment Setup
1. Create `.env.db` file with database credentials
2. Create `.env.backend` file with API configuration

## Configuration Files
### Database Environment (.env.db)
```env
POSTGRES_USER=<username>
POSTGRES_PASSWORD=<password>
POSTGRES_DB=chess_db
POSTGRES_PORT=5432
```

### Backend Environment (.env.backend)
```env
API_BASE_URL=http://localhost:8000
CORS_ORIGINS=["http://localhost:3000"]
```

## Docker Deployment
1. Build the image:
   ```bash
   docker build -t chess-db-backend .
   ```

2. Run the container:
   ```bash
   docker run -d \
     --name chess-db \
     -p 8000:8000 \
     --env-file .env.db \
     --env-file .env.backend \
     chess-db-backend
   ```

## Development Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run migrations:
   ```bash
   alembic upgrade head
   ```

3. Start the development server:
   ```bash
   uvicorn main:app --reload
   ```
