from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class MoveCountAnalysis(BaseModel):
    """Statistical analysis of move counts across chess games"""
    actual_full_moves: int = Field(
        ...,
        description="Number of full moves in game",
        ge=0,
        le=500
    )
    number_of_games: int = Field(
        ...,
        description="Count of games with this move count",
        ge=0
    )
    avg_bytes: float = Field(
        ...,
        description="Average size of encoded game data in bytes",
        ge=0
    )
    results: str = Field(
        ...,
        description="Aggregated game results for this move count"
    )
    min_stored_count: Optional[int] = Field(
        None,
        description="Minimum stored move count",
        ge=0
    )
    max_stored_count: Optional[int] = Field(
        None,
        description="Maximum stored move count",
        ge=0
    )
    avg_stored_count: float = Field(
        ...,
        description="Average stored move count",
        ge=0
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "actual_full_moves": 40,
                "number_of_games": 1000,
                "avg_bytes": 156.5,
                "results": "1-0, 1/2-1/2, 0-1",
                "min_stored_count": 35,
                "max_stored_count": 45,
                "avg_stored_count": 40.5
            }
        }
    )

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class OpeningAnalysis(BaseModel):
    """Detailed analysis of player's performance with a specific opening"""
    eco_code: str = Field(..., description="ECO code of the opening")
    opening_name: str = Field(..., description="Name of the opening")
    total_games: int = Field(..., description="Total games played with this opening")
    win_count: int = Field(..., description="Number of wins with this opening")
    draw_count: int = Field(..., description="Number of draws with this opening")
    loss_count: int = Field(..., description="Number of losses with this opening")
    win_rate: float = Field(..., description="Win rate with this opening")
    avg_game_length: float = Field(..., description="Average game length in moves")
    games_as_white: int = Field(..., description="Games played as white")
    games_as_black: int = Field(..., description="Games played as black")
    avg_opponent_rating: Optional[int] = Field(None, description="Average opponent ELO rating")
    last_played: Optional[datetime] = Field(None, description="Date of most recent game")
    favorite_response: Optional[str] = Field(None, description="Most common response to this opening")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "eco_code": "B07",
                "opening_name": "Pirc Defense",
                "total_games": 42,
                "win_count": 25,
                "draw_count": 10,
                "loss_count": 7,
                "win_rate": 59.52,
                "avg_game_length": 35.8,
                "games_as_white": 20,
                "games_as_black": 22,
                "avg_opponent_rating": 2150,
                "last_played": "2024-03-15T14:30:00",
                "favorite_response": "e4 d6 d4 Nf6"
            }
        }
    )
    
    
class PlayerPerformance(BaseModel):
    """Player performance statistics over a time period"""
    time_period: str = Field(
        ...,
        description="Time period (month/year)",
        examples=["2024-01", "2024"]
    )
    games_played: int = Field(
        ...,
        description="Total games played in period",
        ge=0
    )
    wins: int = Field(
        ...,
        description="Number of wins",
        ge=0
    )
    losses: int = Field(
        ...,
        description="Number of losses",
        ge=0
    )
    draws: int = Field(
        ...,
        description="Number of draws",
        ge=0
    )
    win_rate: float = Field(
        ...,
        description="Win percentage",
        ge=0,
        le=100
    )
    avg_moves: float = Field(
        ...,
        description="Average moves per game",
        ge=0
    )
    white_games: int = Field(
        ...,
        description="Games played as white",
        ge=0
    )
    black_games: int = Field(
        ...,
        description="Games played as black",
        ge=0
    )
    elo_rating: Optional[int] = Field(
        None,
        description="ELO rating if available",
        ge=0,
        le=3000
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "time_period": "2024-01",
                "games_played": 50,
                "wins": 25,
                "losses": 15,
                "draws": 10,
                "win_rate": 62.5,
                "avg_moves": 45.3,
                "white_games": 26,
                "black_games": 24,
                "elo_rating": 2100
            }
        }
    )

    def __init__(self, **data):
        super().__init__(**data)
        # Validate that wins + losses + draws equals games_played
        if self.wins + self.losses + self.draws != self.games_played:
            raise ValueError("Sum of wins, losses, and draws must equal games_played")
        # Validate that white_games + black_games equals games_played
        if self.white_games + self.black_games != self.games_played:
            raise ValueError("Sum of white_games and black_games must equal games_played")


class DatabaseMetrics(BaseModel):
    """Comprehensive database performance and growth metrics"""
    # Current statistics
    total_games: int = Field(..., description="Total number of games in database")
    total_players: int = Field(..., description="Total number of unique players")
    total_openings: int = Field(..., description="Total number of unique openings")
    storage_size: float = Field(..., description="Total database size in MB")
    
    # Performance metrics
    avg_query_time: float = Field(..., description="Average query response time in milliseconds")
    queries_per_second: float = Field(..., description="Average queries processed per second")
    cache_hit_ratio: float = Field(..., description="Cache hit ratio percentage")
    
    # Time-based metrics
    growth_trend: List[GrowthMetric] = Field(
        ..., 
        description="Database growth metrics over time"
    )
    query_performance: List[QueryPerformanceMetric] = Field(
        ...,
        description="Query performance statistics"
    )
    
    # Health indicators
    index_health: float = Field(
        ..., 
        description="Index efficiency score (0-100)"
    )
    replication_lag: Optional[float] = Field(
        None,
        description="Replication lag in seconds, if applicable"
    )
    
    # System capacity
    capacity_used: float = Field(
        ...,
        description="Percentage of total capacity used"
    )
    estimated_capacity_date: Optional[datetime] = Field(
        None,
        description="Estimated date when capacity will be reached"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_games": 1000000,
                "total_players": 50000,
                "total_openings": 500,
                "storage_size": 1024.5,
                "avg_query_time": 45.2,
                "queries_per_second": 100.5,
                "cache_hit_ratio": 85.5,
                "growth_trend": [
                    {
                        "date": "2024-01-01T00:00:00",
                        "total_games": 900000,
                        "total_players": 45000,
                        "storage_used": 950.5
                    }
                ],
                "query_performance": [
                    {
                        "query_type": "game_search",
                        "avg_execution_time": 35.5,
                        "calls_per_minute": 120.0,
                        "error_rate": 0.1
                    }
                ],
                "index_health": 95.5,
                "replication_lag": 0.5,
                "capacity_used": 65.5,
                "estimated_capacity_date": "2024-12-01T00:00:00"
            }
        }
    )
