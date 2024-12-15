from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# SQLAlchemy Model
class ItemDB(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models for API
class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(ItemBase):
    name: Optional[str] = None

class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PlayerResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class PlayerDB(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

class GameDB(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    white_player_id = Column(Integer, ForeignKey("players.id"))
    black_player_id = Column(Integer, ForeignKey("players.id"))
    date = Column(Date)
    result = Column(String(10))
    eco = Column(String(10))
    moves = Column(Text)
    
    white_player = relationship("PlayerDB", foreign_keys=[white_player_id])
    black_player = relationship("PlayerDB", foreign_keys=[black_player_id])

# Pydantic Models for API
class GameResponse(BaseModel):
    id: int
    white_player_id: int
    black_player_id: int
    white_player: Optional[PlayerResponse] = None
    black_player: Optional[PlayerResponse] = None
    date: Optional[datetime] = None
    result: str
    eco: Optional[str] = None
    moves: str
    model_config = ConfigDict(from_attributes=True)



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

class PlayerPerformanceResponse(BaseModel):
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

class OpeningStatsResponse(BaseModel):
    """Statistical analysis of player's performance with specific openings"""
    eco_code: str = Field(
        ...,
        description="ECO code of the opening",
        min_length=3,
        max_length=3,
        pattern="^[A-E][0-9]{2}$"  # Updated from regex to pattern
    )
    opening_name: str = Field(
        ...,
        description="Name of the opening",
        min_length=1
    )
    games_played: int = Field(
        ...,
        description="Number of games with this opening",
        ge=0
    )
    win_rate: float = Field(
        ...,
        description="Win rate with this opening",
        ge=0,
        le=100
    )
    avg_moves: float = Field(
        ...,
        description="Average game length with this opening",
        ge=0
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "eco_code": "E04",
                "opening_name": "Catalan Opening",
                "games_played": 150,
                "win_rate": 58.5,
                "avg_moves": 42.7
            }
        }
    )

class PlayerSearchResponse(BaseModel):
    """Player search result with name and rating information"""
    id: int
    name: str
    elo: Optional[int] = None
    
    class Config:
        from_attributes = True

        
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class QueryPerformanceMetric(BaseModel):
    """Statistics for database query performance"""
    query_type: str = Field(..., description="Type of query or operation")
    avg_execution_time: float = Field(..., description="Average execution time in milliseconds")
    calls_per_minute: float = Field(..., description="Average number of calls per minute")
    error_rate: float = Field(..., description="Percentage of failed queries")

class GrowthMetric(BaseModel):
    """Time-series data point for database growth metrics"""
    date: datetime = Field(..., description="Timestamp for the metric")
    total_games: int = Field(..., description="Cumulative number of games")
    total_players: int = Field(..., description="Cumulative number of players")
    storage_used: float = Field(..., description="Storage space used in MB")

class DatabaseMetricsResponse(BaseModel):
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

class OpeningAnalysisResponse(BaseModel):
    """Response model for opening analysis endpoint"""
    analysis: List[OpeningAnalysis]
    total_openings: int = Field(..., description="Total number of distinct openings played")
    most_successful: Optional[str] = Field(None, description="ECO code with highest win rate")
    most_played: Optional[str] = Field(None, description="Most frequently played ECO code")
    avg_game_length: float = Field(..., description="Average game length across all openings")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "analysis": [
                    {
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
                ],
                "total_openings": 15,
                "most_successful": "B07",
                "most_played": "E04",
                "avg_game_length": 38.5
            }
        }
    )

class DetailedPerformanceResponse(BaseModel):
    """Enhanced player performance statistics over a time period"""
    time_period: str = Field(..., description="Time period of analysis")
    games_played: int = Field(..., description="Total games played")
    wins: int = Field(..., description="Number of wins")
    losses: int = Field(..., description="Number of losses")
    draws: int = Field(..., description="Number of draws")
    win_rate: float = Field(..., description="Win percentage")
    avg_moves: float = Field(..., description="Average moves per game")
    white_games: int = Field(..., description="Games played as white")
    black_games: int = Field(..., description="Games played as black")
    avg_elo: Optional[int] = Field(None, description="Average ELO rating")
    elo_change: Optional[int] = Field(None, description="ELO rating change")
    opening_diversity: float = Field(..., description="Opening diversity score")
    avg_game_length: float = Field(..., description="Average game length")

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
                "avg_elo": 2100,
                "elo_change": 15,
                "opening_diversity": 0.85,
                "avg_game_length": 42.7
            }
        }
    )

class AnalyticsParameters(BaseModel):
    """Parameters for analytics queries"""
    time_grouping: str = Field(
        "month",
        description="Time period grouping (day, week, month, year)"
    )
    start_date: Optional[str] = Field(None, description="Start date for analysis")
    end_date: Optional[str] = Field(None, description="End date for analysis")
    min_games: Optional[int] = Field(5, description="Minimum games threshold")
    time_period: Optional[str] = Field(
        None,
        description="Time period filter (1y, 6m, 3m, 1m)"
    )