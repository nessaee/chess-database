from .base import (
    Base, Column, Integer, String, Text, DateTime,
    ForeignKey, relationship, BaseModel, ConfigDict, Field
)
from typing import List, Optional, Dict, Any
from datetime import datetime

class MoveCountAnalysis(BaseModel):
    """Statistical analysis of move counts across chess games"""
    actual_full_moves: int = Field(..., description="Number of full moves in game", ge=0, le=500)
    number_of_games: int = Field(..., description="Count of games with this move count", ge=0)
    avg_bytes: float = Field(..., description="Average size of encoded game data in bytes", ge=0)
    results: str = Field(..., description="Aggregated game results for this move count")
    min_stored_count: Optional[int] = Field(None, description="Minimum stored move count")
    max_stored_count: Optional[int] = Field(None, description="Maximum stored move count")
    avg_stored_count: float = Field(..., description="Average stored move count")

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
                }
            }
        }
    )
