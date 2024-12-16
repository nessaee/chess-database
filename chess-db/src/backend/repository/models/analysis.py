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

class OpeningStatsResponse(BaseModel):
    """Statistical analysis of player's performance with specific openings"""
    eco_code: str = Field(..., description="ECO code of the opening", min_length=3, max_length=3, pattern="^[A-E][0-9]{2}$")
    opening_name: str = Field(..., description="Name of the opening", min_length=1)
    games_played: int = Field(..., description="Number of games with this opening", ge=0)
    win_rate: float = Field(..., description="Win rate with this opening", ge=0, le=100)
    avg_moves: float = Field(..., description="Average game length with this opening", ge=0)

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

class DatabaseMetricsResponse(BaseModel):
    """Overall database metrics and statistics"""
    total_games: int = Field(..., description="Total number of games in database")
    total_players: int = Field(..., description="Total number of unique players")
    date_range: Dict[str, datetime] = Field(..., description="Earliest and latest game dates")
    storage_metrics: Dict[str, float] = Field(..., description="Database storage statistics in bytes")
    game_stats: Dict[str, float] = Field(..., description="Game statistics including averages and counts")
    rating_distribution: Dict[str, int] = Field(..., description="Distribution of player ratings")
    last_update: datetime = Field(..., description="Last database update timestamp")
    model_config = ConfigDict(from_attributes=True)
