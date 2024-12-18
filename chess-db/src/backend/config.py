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

# Get the absolute paths to environment files
# Check if we're running in Docker (where files will be in /app) or local development
if os.path.exists('/app'):
    PROJECT_ROOT = Path('/app')
else:
    BACKEND_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = BACKEND_DIR.parent

env_db = PROJECT_ROOT / ".env.db"
env_backend = PROJECT_ROOT / ".env.backend"

# For debugging
print(f"Looking for env files at:")
print(f"- DB env: {env_db}")
print(f"- Backend env: {env_backend}")

if not env_db.exists():
    raise FileNotFoundError(f"Required .env.db file not found. Tried path: {env_db}")
if not env_backend.exists():
    raise FileNotFoundError(f"Required .env.backend file not found. Tried path: {env_backend}")

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
# TEST_DB_NAME = get_required_env("TEST_DB_NAME")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# TEST_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}"

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