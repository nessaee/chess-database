"""
Repository package for the chess database.

This package contains all the database repositories and their implementations.
Each repository is responsible for a specific domain of the chess database
and provides methods for querying and manipulating that domain's data.
"""

from .game.repository import GameRepository
from .player.repository import PlayerRepository
from .analysis.repository import AnalysisRepository

# Version info
__version__ = '1.0.0'
__author__ = 'ECE501C Team'

__all__ = [
    # Repository classes
    'GameRepository',
    'PlayerRepository',
    'AnalysisRepository',
    
    # Version info
    '__version__',
    '__author__'
]
