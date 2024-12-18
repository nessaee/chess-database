from .base import (
    Base, Column, Integer, String, Text, DateTime,
    ForeignKey, relationship, BaseModel, ConfigDict, Field
)
from typing import List, Optional, Dict, Any
from datetime import datetime

class MoveCountAnalysis(BaseModel):
    """Statistical analysis of move counts across chess games"""
    move_count: int = Field(..., description="Number of full moves in game", ge=0, le=500)
    game_count: int = Field(..., description="Count of games with this move count", ge=0)
    avg_bytes: float = Field(..., description="Average size of encoded game data in bytes", ge=0)

class PlayerPerformanceResponse(BaseModel):
    """Player performance statistics over a time period"""
    time_period: str = Field(..., description="Time period (month/year)", examples=["2024-01", "2024"])
    games_played: int = Field(..., description="Total games played in period", ge=0)
    wins: int = Field(..., description="Number of wins", ge=0)
    losses: int = Field(..., description="Number of losses", ge=0)
    draws: int = Field(..., description="Number of draws", ge=0)
    win_rate: float = Field(..., description="Win percentage", ge=0, le=100)
    avg_moves: float = Field(..., description="Average moves per game", ge=0)
    white_games: int = Field(..., description="Games played as white", ge=0)
    black_games: int = Field(..., description="Games played as black", ge=0)
    elo_rating: Optional[int] = Field(None, description="ELO rating if available", ge=0, le=3000)

    def __init__(self, **data):
        super().__init__(**data)
        if self.wins + self.losses + self.draws != self.games_played:
            raise ValueError("Sum of wins, losses, and draws must equal games_played")
        if self.white_games + self.black_games != self.games_played:
            raise ValueError("Sum of white_games and black_games must equal games_played")

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

class OpeningAnalysis(BaseModel):
    """Detailed analysis of player's performance with a specific opening"""
    message: str = Field(..., description="Message")
    type: str = Field(..., description="Type")
    opening_name: str = Field(..., description="Name of the opening")
    total_games: int = Field(..., description="Total games played with this opening")
    win_count: int = Field(..., description="Number of wins with this opening")
    draw_count: int = Field(..., description="Number of draws with this opening")
    loss_count: int = Field(..., description="Number of losses with this opening")
    win_rate: float = Field(..., description="Win rate with this opening")
    avg_game_length: float = Field(..., description="Average game length in moves")
    games_as_white: int = Field(..., description="Games played as white")
    games_as_black: int = Field(..., description="Games played as black")
    variations: List[str] = Field(default_factory=list, description="List of variations")

class OpeningAnalysisResponse(BaseModel):
    """Opening statistics for a specific player"""
    analysis: List[OpeningAnalysis] = Field(default_factory=list, description="List of all openings")
    total_openings: int = Field(..., description="Total number of unique openings")
    avg_game_length: float = Field(..., description="Average game length in moves")
    total_games: int = Field(..., description="Total games analyzed")
    total_wins: int = Field(..., description="Total number of wins")
    total_draws: int = Field(..., description="Total number of draws")
    total_losses: int = Field(..., description="Total number of losses")
    most_successful: str = Field(..., description="Most successful opening")
    most_played: str = Field(..., description="Most frequently played opening")

class EndpointMetrics(BaseModel):
    """Performance metrics for an API endpoint"""
    endpoint: str = Field(..., description="API endpoint path")
    method: str = Field(..., description="HTTP method")
    total_calls: int = Field(..., description="Total number of calls")
    successful_calls: int = Field(..., description="Number of successful calls")
    avg_response_time: float = Field(..., description="Average response time in milliseconds")
    p95_response_time: float = Field(..., description="95th percentile response time")
    p99_response_time: float = Field(..., description="99th percentile response time")
    max_response_time: float = Field(..., description="Maximum response time")
    min_response_time: float = Field(..., description="Minimum response time")
    error_count: int = Field(..., description="Number of errors")
    success_rate: float = Field(..., description="Success rate percentage")
    error_rate: float = Field(..., description="Error rate percentage")
    avg_response_size: float = Field(..., description="Average response size in bytes")
    max_response_size: int = Field(..., description="Maximum response size in bytes")
    min_response_size: int = Field(..., description="Minimum response size in bytes")

class DetailedPerformanceResponse(BaseModel):
    """Detailed performance statistics for a player."""
    
    # Player information
    player_id: int
    total_games: int
    
    # Performance metrics
    win_rate: float = Field(default=0.0)
    draw_rate: float = Field(default=0.0)
    loss_rate: float = Field(default=0.0)
    
    # Opening statistics
    opening_diversity: float = Field(default=0.0)
    favorite_opening: str = Field(default="")
    opening_win_rate: float = Field(default=0.0)
    
    # Time control statistics
    avg_game_length: float = Field(default=0.0)
    time_control_preference: str = Field(default="")
    
    # Positional statistics
    piece_placement_accuracy: float = Field(default=0.0)
    tactical_accuracy: float = Field(default=0.0)
    
    # Recent performance
    recent_performance_trend: float = Field(default=0.0)
    last_updated: datetime = Field(default_factory=datetime.now)

class DatabaseMetricsResponse(BaseModel):
    """Overall database metrics and statistics"""
    total_games: int = Field(..., description="Total number of games in database")
    total_players: int = Field(..., description="Total number of unique players")
    avg_moves_per_game: float = Field(..., description="Average number of moves per game")
    avg_game_duration: float = Field(..., description="Average game duration in seconds")
    
    # Performance metrics
    performance: Dict[str, float] = Field(
        ...,
        description="Game performance metrics including win rates and draw rates"
    )
    
    # Growth trends
    growth_trends: Dict[str, float] = Field(
        ...,
        description="Database growth metrics including monthly averages and peaks"
    )
    
    # Health metrics
    health_metrics: Dict[str, float] = Field(
        ...,
        description="Database health metrics including data quality indicators"
    )

    # Endpoint performance metrics
    endpoint_metrics: List[EndpointMetrics] = Field(
        default_factory=list,
        description="Performance metrics for API endpoints"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_games": 100000,
                "total_players": 5000,
                "avg_moves_per_game": 40.5,
                "avg_game_duration": 1800.0,
                "performance": {
                    "white_win_rate": 0.52,
                    "draw_rate": 0.15,
                    "avg_game_length": 42.3
                },
                "growth_trends": {
                    "avg_monthly_games": 1200.5,
                    "avg_monthly_players": 450.2,
                    "peak_monthly_games": 2500,
                    "peak_monthly_players": 800
                },
                "health_metrics": {
                    "null_moves_rate": 0.02,
                    "missing_player_rate": 0.01,
                    "missing_result_rate": 0.03
                },
                "endpoint_metrics": [
                    {
                        "endpoint": "/api/games",
                        "method": "GET",
                        "total_calls": 10000,
                        "successful_calls": 9900,
                        "avg_response_time": 50.2,
                        "p95_response_time": 100.5,
                        "p99_response_time": 150.8,
                        "max_response_time": 200.1,
                        "min_response_time": 20.5,
                        "error_count": 100,
                        "success_rate": 99.0,
                        "error_rate": 1.0,
                        "avg_response_size": 1024.0,
                        "max_response_size": 2048,
                        "min_response_size": 512
                    }
                ]
            }
        }
    )
