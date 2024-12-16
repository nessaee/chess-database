"""
Models package for the chess database repository.

This package contains all the database models and response models used in the chess database.
Models are organized by domain (game, player, analysis) and include both SQLAlchemy ORM models
and Pydantic response models.
"""

from .base import *
from .game import GameDB, GameResponse
from .player import PlayerDB, PlayerResponse, PlayerSearchResponse, PlayerPerformanceResponse, DetailedPerformanceResponse
from .analysis import (
    MoveCountAnalysis,
    OpeningStatsResponse,
    OpeningAnalysis,
    OpeningAnalysisResponse,
    DatabaseMetricsResponse
)

__all__ = [
    # Base models and types
    'Base', 'Column', 'Integer', 'String', 'Text', 'DateTime', 'Date',
    'ForeignKey', 'relationship', 'BaseModel', 'ConfigDict',
    
    # Game models
    'GameDB', 'GameResponse',
    
    # Player models
    'PlayerDB', 'PlayerResponse', 'PlayerSearchResponse',
    'PlayerPerformanceResponse', 'DetailedPerformanceResponse',
    
    # Analysis models
    'MoveCountAnalysis', 'OpeningStatsResponse',
    'OpeningAnalysis', 'OpeningAnalysisResponse',
    'DatabaseMetricsResponse'
]
