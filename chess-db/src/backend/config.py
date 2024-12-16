# config.py
from typing import List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_VERSION = "1.0.0"

# Database Configuration
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "chesspass")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "chess")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Cache Configuration
CACHE_TTL = 300  # 5 minutes
CACHE_CONTROL_HEADER = "public, max-age=300"  # 5 minutes

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "api.log"

# CORS Configuration
CORS_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://frontend:5173",
    "http://192.168.1.30:5173",
    "http://web:8000",
    "*"  # Allow all origins in development
]

# API Rate Limiting
RATE_LIMIT = "100/minute"