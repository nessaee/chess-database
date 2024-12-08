from dataclasses import dataclass
import os

@dataclass
class DatabaseConfig:
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', 5433))
    database: str = os.getenv('DB_NAME', 'chess')
    user: str = os.getenv('DB_USER', 'postgres')
    password: str = os.getenv('DB_PASSWORD', 'chesspass')