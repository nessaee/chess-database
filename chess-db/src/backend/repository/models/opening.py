"""
Models for opening analysis using the game_opening_matches materialized view.
"""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field

class OpeningVariationStats(BaseModel):
    """Statistics for a specific opening variation"""
    name: str = Field(..., description="Variation name")
    games_played: int = Field(..., description="Total number of games")
    wins: int = Field(..., description="Number of wins")
    draws: int = Field(..., description="Number of draws")
    losses: int = Field(..., description="Number of losses")
    win_rate: float = Field(..., description="Win rate percentage")
    draw_rate: float = Field(..., description="Draw rate percentage")

class OpeningStats(BaseModel):
    """Basic opening statistics"""
    name: str = Field(..., description="Opening name")
    games_played: int = Field(..., description="Total number of games")
    wins: int = Field(..., description="Number of wins")
    draws: int = Field(..., description="Number of draws")
    losses: int = Field(..., description="Number of losses")
    win_rate: float = Field(..., description="Win rate percentage")
    draw_rate: float = Field(..., description="Draw rate percentage")
    white_games: int = Field(..., description="Games played as white")
    black_games: int = Field(..., description="Games played as black")
    variations: List[OpeningVariationStats] = Field(default_factory=list, description="List of variations within this opening")

class AnalysisInsight(BaseModel):
    """A single analysis insight"""
    message: str = Field(..., description="Analysis message")
    type: str = Field(..., description="Type of insight (e.g., 'win_rate', 'best_opening')")
    eco_code: str = Field("", description="ECO code (deprecated)")
    opening_name: str = Field(..., description="Opening name")
    total_games: int = Field(..., description="Total number of games")
    win_count: int = Field(..., description="Number of wins")
    draw_count: int = Field(..., description="Number of draws")
    loss_count: int = Field(..., description="Number of losses")
    win_rate: float = Field(..., description="Win rate percentage")
    avg_game_length: float = Field(..., description="Average game length")
    games_as_white: int = Field(..., description="Games played as white")
    games_as_black: int = Field(..., description="Games played as black")
    avg_opponent_rating: Optional[float] = Field(None, description="Average opponent rating")
    last_played: Optional[date] = Field(None, description="Date last played")
    favorite_response: Optional[str] = Field(None, description="Most common response")
    variations: List[OpeningVariationStats] = Field(default_factory=list, description="List of variations within this opening")

class OpeningAnalysisResponse(BaseModel):
    """Opening statistics for a specific player"""
    openings: List[OpeningStats] = Field(default_factory=list, description="List of all openings")
    analysis: List[AnalysisInsight] = Field(default_factory=list, description="List of analysis insights")
    total_openings: int = Field(0, description="Total number of unique openings")
    avg_game_length: float = Field(0.0, description="Average game length in moves")
    total_games: int = Field(..., description="Total games analyzed")
    total_wins: int = Field(..., description="Total number of wins")
    total_draws: int = Field(..., description="Total number of draws")
    total_losses: int = Field(..., description="Total number of losses")
    most_successful: Optional[str] = Field(None, description="Most successful opening")
    most_played: Optional[str] = Field(None, description="Most frequently played opening")

class PopularOpeningStats(BaseModel):
    """Statistics for popular openings"""
    eco: str = Field(..., description="ECO code")
    name: str = Field(..., description="Opening name")
    total_games: int = Field(..., description="Total number of games")
    white_win_rate: float = Field(..., description="Win rate for white")
    unique_players: int = Field(..., description="Number of unique players")
    variations: List[OpeningVariationStats] = Field(default_factory=list, description="List of opening variations within this ECO")
