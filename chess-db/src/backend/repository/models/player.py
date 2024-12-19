from .base import (
    Base, Column, Integer, String,
    BaseModel, ConfigDict, Field
)
from typing import Optional
from datetime import datetime

class PlayerDB(Base):
    """Database model for chess players"""
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

class PlayerResponse(BaseModel):
    """Basic player information response"""
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class PlayerSearchResponse(BaseModel):
    """Player search result with name and rating information"""
    id: int
    name: str
    elo: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class PlayerPerformanceResponse(BaseModel):
    """Basic player performance metrics"""
    games_played: int
    wins: int
    losses: int
    draws: int
    win_rate: float
    avg_elo: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class DetailedPerformanceResponse(PlayerPerformanceResponse):
    """Detailed player performance metrics with time period information"""
    time_period: str
    avg_moves: float
    white_games: int
    black_games: int
    elo_change: Optional[int] = None
    opening_diversity: float = Field(ge=0.0, le=1.0, description="Ratio of unique openings to total games")
    avg_game_length: float
    model_config = ConfigDict(from_attributes=True)
