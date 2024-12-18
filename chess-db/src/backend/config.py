from typing import List
import os
from dotenv import load_dotenv
from pathlib import Path

def get_required_env(key: str) -> str:
    """Get a required environment variable or raise an error."""
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

# Check if environment files exist
env_db = Path("../.env.db")
env_backend = Path("../.env.backend")

if not env_db.exists():
    raise FileNotFoundError("Required .env.db file not found")
if not env_backend.exists():
    raise FileNotFoundError("Required .env.backend file not found")

# Load environment variables from both files
load_dotenv(env_db)  # Load database config first
load_dotenv(env_backend, override=True)  # Override with backend-specific config

# API Configuration
API_VERSION = "1.0.0"
API_BASE_URL = get_required_env("API_BASE_URL")

# Database Configuration - All required from environment
DB_USER = get_required_env("POSTGRES_USER")
DB_PASS = get_required_env("POSTGRES_PASSWORD")
DB_HOST = get_required_env("DB_HOST")
DB_PORT = get_required_env("POSTGRES_PORT")
DB_NAME = get_required_env("POSTGRES_DB")
TEST_DB_NAME = get_required_env("TEST_DB_NAME")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
TEST_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}"

# Cache Configuration
CACHE_TTL = int(get_required_env("CACHE_TTL"))
CACHE_CONTROL_HEADER = "Cache-Control"
CACHE_CONTROL_VALUE = f"public, max-age={CACHE_TTL}"

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = get_required_env("LOG_FILE")
LOG_LEVEL = get_required_env("LOG_LEVEL")

# CORS Configuration
CORS_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://frontend:5173",
    "http://web:8000",
    "*"  # Allow all origins in development
]

# API Rate Limiting
RATE_LIMIT = get_required_env("RATE_LIMIT")