"""
Router package for the chess database API.
Contains all FastAPI routers for different endpoints.
"""

from .analysis import router as analysis_router
from .games import router as game_router
from .players import router as player_router
from .database import router as database_router

__all__ = [
    'analysis_router',
    'game_router',
    'player_router',
    'database_router'
]
