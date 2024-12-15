# config.py
from typing import List
import os

# API Configuration
API_VERSION = "1.0.0"

# CORS Configuration
CORS_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://frontend:5173",
    "http://192.168.1.30:5173"
]

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:chesspass@localhost:5433/chess"
)

# Cache Configuration
CACHE_TTL = 300  # 5 minutes
CACHE_CONTROL_HEADER = f"public, max-age={CACHE_TTL}"

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "api.log"

# API Rate Limiting
RATE_LIMIT = "100/minute"