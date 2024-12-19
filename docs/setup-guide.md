---
layout: default
title: Setup Guide
description: Instructions for setting up the Chess Database development environment
---

# Setup Guide

This guide will help you set up your development environment for the Chess Database project.

## Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/nessaee/chess-database.git
cd chess-database
```

2. Set up environment variables:
```bash
cp .env.example .env
```

3. Start the services:
```bash
docker-compose up -d
```

## Detailed Setup

### Backend Setup

1. Create a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Set up the database:
```bash
alembic upgrade head
```

4. Start the development server:
```bash
uvicorn main:app --reload
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chess_db
DB_USER=postgres
DB_PASSWORD=your_password

# API
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true

# Frontend
VITE_API_URL=http://localhost:8000
```

### Database Configuration

1. Create a new PostgreSQL database:
```sql
CREATE DATABASE chess_db;
```

2. Apply migrations:
```bash
alembic upgrade head
```

## Verification

1. Access the API documentation:
```
http://localhost:8000/docs
```

2. Access the frontend:
```
http://localhost:3000
```

## Common Issues

### Database Connection

If you encounter database connection issues:

1. Verify PostgreSQL is running:
```bash
sudo systemctl status postgresql
```

2. Check connection settings in `.env`

### Frontend Build

If the frontend build fails:

1. Clear npm cache:
```bash
npm cache clean --force
```

2. Remove and reinstall dependencies:
```bash
rm -rf node_modules
npm install
```

## Next Steps

- Read the [Architecture Overview](architecture.md)
- Explore the [API Reference](api-reference.md)
- Start [Development](development-guide.md)
