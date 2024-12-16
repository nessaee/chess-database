# repository/player/types.py
from typing import TypeVar, Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel, Field

class PlayerFilter(BaseModel):
    """Filter parameters for player queries."""
    min_rating: Optional[int] = None
    max_rating: Optional[int] = None
    active_since: Optional[datetime] = None
    min_games: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "min_rating": 2000,
                "max_rating": 2500,
                "active_since": "2024-01-01",
                "min_games": 10
            }
        }

class PlayerSort(BaseModel):
    """Sorting options for player queries."""
    field: str  # 'name', 'rating', 'games_played'
    ascending: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "field": "rating",
                "ascending": False
            }
        }

@dataclass
class PlayerQueryParams:
    """Combined query parameters for player repository operations."""
    filters: Optional[PlayerFilter] = None
    sort: Optional[PlayerSort] = None
    limit: Optional[int] = None
    offset: Optional[int] = None



class PlayerStats(BaseModel):
    """Statistical summary of a player's performance."""
    total_games: int = Field(..., ge=0)
    wins: int = Field(..., ge=0)
    losses: int = Field(..., ge=0)
    draws: int = Field(..., ge=0)
    win_rate: float = Field(..., ge=0, le=100)
    avg_game_length: float = Field(..., ge=0)
    
    class Config:
        validate_assignment = True

@dataclass
class RatingProgress:
    """Track a player's rating progression over time."""
    current_rating: Optional[int]
    peak_rating: Optional[int]
    min_rating: Optional[int]
    avg_rating: float
    rating_volatility: float
    last_change: int
    trend: float  # Points per month

class OpponentAnalysis(BaseModel):
    """Analysis of performance against different opponent levels."""
    category: str = Field(..., regex="^(grandmaster|international_master|master|expert|other)$")
    games_played: int = Field(..., ge=0)
    score_percentage: float = Field(..., ge=0, le=100)
    avg_rating: Optional[int] = Field(None, ge=0, le=3500)

class OpeningAnalysis(BaseModel):
    """Analysis of performance with specific openings."""
    eco: str = Field(..., regex="^[A-E][0-9]{2}$")
    games_played: int = Field(..., ge=0)
    score_percentage: float = Field(..., ge=0, le=100)
    avg_length: float = Field(..., ge=0)
    wins: int = Field(..., ge=0)
    draws: int = Field(..., ge=0)
    
    @property
    def losses(self) -> int:
        return self.games_played - (self.wins + self.draws)

class PlayingStyle(BaseModel):
    """Analysis of a player's playing style characteristics."""
    avg_game_length: float = Field(..., ge=0)
    game_length_variance: float = Field(..., ge=0)
    opening_diversity: float = Field(..., ge=0, le=1)
    decisive_percentage: float = Field(..., ge=0, le=100)
    color_preference: float = Field(..., ge=-1, le=1)  # -1 (black) to 1 (white)
    
    class Config:
        validate_assignment = True

class TimelineEntry(BaseModel):
    """Performance metrics for a specific time period."""
    period: datetime
    games_played: int = Field(..., ge=0)
    win_rate: float = Field(..., ge=0, le=100)
    avg_rating: Optional[int] = Field(None, ge=0)
    rating_change: Optional[int]
    performance_rating: Optional[int] = Field(None, ge=0)

class CompleteAnalysis(BaseModel):
    """Comprehensive player analysis including all aspects."""
    stats: PlayerStats
    ratings: RatingProgress
    openings: List[OpeningAnalysis]
    timeline: List[TimelineEntry]
    opponents: List[OpponentAnalysis]
    style: PlayingStyle
    
    class Config:
        validate_assignment = True

def validate_analysis_data(data: Dict[str, Any]) -> CompleteAnalysis:
    """
    Validate and convert raw analysis data to typed objects.
    
    Args:
        data: Raw analysis data from database
        
    Returns:
        CompleteAnalysis object with validated data
        
    Raises:
        ValueError: If data validation fails
    """
    try:
        return CompleteAnalysis(
            stats=PlayerStats(**data['stats']),
            ratings=RatingProgress(**data['ratings']),
            openings=[OpeningAnalysis(**o) for o in data['openings']],
            timeline=[TimelineEntry(**t) for t in data['timeline']],
            opponents=[OpponentAnalysis(**o) for o in data['opponents']],
            style=PlayingStyle(**data['style'])
        )
    except Exception as e:
        raise ValueError(f"Invalid analysis data: {str(e)}")