"""
Models for opening analysis using the game_opening_matches materialized view.
"""

from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import json

class OpeningVariationStats(BaseModel):
    """Statistics for a specific opening variation"""
    name: str = Field(..., description="Full opening name including variation")
    games_played: int = Field(..., description="Total number of games")
    wins: int = Field(..., description="Number of wins")
    draws: int = Field(..., description="Number of draws")
    losses: int = Field(..., description="Number of losses")
    win_rate: float = Field(..., description="Win rate percentage")
    draw_rate: float = Field(..., description="Draw rate percentage")

class TrendData(BaseModel):
    """Trend data model with parallel arrays for months, games, and win rates."""
    months: List[str] = Field(default_factory=list)
    games: List[int] = Field(default_factory=list)
    win_rates: List[float] = Field(default_factory=list)

    class Config:
        """Model configuration."""
        from_attributes = True
        populate_by_name = True
        allow_population_by_field_name = True
        json_schema_extra = {
            "example": {
                "months": ["2024-01", "2024-02", "2024-03"],
                "games": [10, 15, 20],
                "win_rates": [60.0, 65.5, 70.0]
            }
        }

    @classmethod
    def from_json(cls, json_str: str) -> "TrendData":
        """Create TrendData from JSON string or dictionary."""
        if not json_str:
            return cls()
        try:
            if isinstance(json_str, dict):
                return cls(**json_str)
            data = json.loads(json_str) if isinstance(json_str, str) else json_str
            return cls(
                months=data.get("months", []),
                games=data.get("games", []),
                win_rates=data.get("win_rates", [])
            )
        except (json.JSONDecodeError, AttributeError):
            return cls()

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "months": self.months,
            "games": self.games,
            "win_rates": self.win_rates
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.dict())

class OpeningStats(BaseModel):
    """Opening statistics model."""
    opening_name: str = Field(..., description="Full opening name")
    name: str = Field(..., description="Full opening name", alias="opening_name")
    total_games: int = Field(..., description="Total number of games")
    win_count: int = Field(..., description="Number of wins")
    wins: int = Field(..., description="Number of wins", alias="win_count")
    draw_count: int = Field(..., description="Number of draws")
    draws: int = Field(..., description="Number of draws", alias="draw_count")
    loss_count: int = Field(..., description="Number of losses")
    losses: int = Field(..., description="Number of losses", alias="loss_count")
    win_rate: float = Field(..., description="Win rate percentage")
    games_as_white: int = Field(..., description="Games played as white")
    games_as_black: int = Field(..., description="Games played as black")
    avg_game_length: float = Field(..., description="Average game length in moves")
    trend_data: TrendData = Field(default_factory=TrendData, description="Monthly trend data")
    message: str = Field(..., description="Analysis message")
    type: str = Field(..., description="Type of insight")
    variations: List[Dict[str, Any]] = Field(default_factory=list, description="List of variations")

    @property
    def draw_rate(self) -> float:
        """Calculate draw rate."""
        if not self.total_games:
            return 0.0
        return round((self.draw_count / self.total_games) * 100, 1)

    @property
    def loss_rate(self) -> float:
        """Calculate loss rate."""
        if not self.total_games:
            return 0.0
        return round((self.loss_count / self.total_games) * 100, 1)

    def __init__(self, **data):
        """Initialize OpeningStats with custom handling for trend_data."""
        if "trend_data" in data and isinstance(data["trend_data"], str):
            data["trend_data"] = TrendData.from_json(data["trend_data"])
        super().__init__(**data)

    class Config:
        """Model configuration."""
        from_attributes = True
        populate_by_name = True
        allow_population_by_field_name = True
        json_encoders = {
            TrendData: lambda v: v.dict()
        }

class AnalysisInsight(BaseModel):
    """A single analysis insight"""
    message: str = Field(..., description="Analysis message")
    type: str = Field(..., description="Type of insight (e.g., 'win_rate', 'opening_stats')")
    opening_name: str = Field(..., description="Full opening name")
    total_games: int = Field(..., description="Total number of games")
    win_count: int = Field(..., description="Number of wins")
    draw_count: int = Field(..., description="Number of draws")
    loss_count: int = Field(..., description="Number of losses")
    win_rate: float = Field(..., description="Win rate percentage")
    avg_game_length: float = Field(..., description="Average game length in moves")
    games_as_white: int = Field(..., description="Games played as white")
    games_as_black: int = Field(..., description="Games played as black")
    avg_opponent_rating: Optional[float] = Field(None, description="Average opponent rating")
    last_played: Optional[date] = Field(None, description="Date last played")
    favorite_response: Optional[str] = Field(None, description="Most common response")
    max_win_rate: float = Field(..., description="Maximum win rate achieved")
    trend_data: List[Dict[str, Any]] = Field(default_factory=list, description="Monthly trend data for opening frequency")
    variations: List[Dict[str, Any]] = Field(default_factory=list, description="List of variations")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        data = self.model_dump()
        # Convert None values to appropriate types for optional fields
        if data['avg_opponent_rating'] is None:
            data['avg_opponent_rating'] = 0.0
        if data['last_played'] is None:
            data['last_played'] = ""
        if data['favorite_response'] is None:
            data['favorite_response'] = ""
        return data

class OpeningAnalysisResponse(BaseModel):
    """Opening analysis response model."""
    analysis: List[OpeningStats] = Field(default_factory=list)
    total_openings: int = Field(default=0)
    avg_game_length: float = Field(default=0.0)
    total_games: int = Field(default=0)
    total_wins: int = Field(default=0)
    total_draws: int = Field(default=0)
    total_losses: int = Field(default=0)
    most_successful: str = Field(default="No openings found")
    most_played: str = Field(default="No openings found")
    trend_data: TrendData = Field(default_factory=TrendData)

    def __init__(self, **data):
        """Initialize OpeningAnalysisResponse with custom handling for trend_data."""
        if "trend_data" in data and isinstance(data["trend_data"], str):
            data["trend_data"] = TrendData.from_json(data["trend_data"])
        super().__init__(**data)

    @property
    def win_rate(self) -> float:
        """Calculate overall win rate."""
        if not self.total_games:
            return 0.0
        return round((self.total_wins / self.total_games) * 100, 1)

    @property
    def draw_rate(self) -> float:
        """Calculate overall draw rate."""
        if not self.total_games:
            return 0.0
        return round((self.total_draws / self.total_games) * 100, 1)

    @property
    def loss_rate(self) -> float:
        """Calculate overall loss rate."""
        if not self.total_games:
            return 0.0
        return round((self.total_losses / self.total_games) * 100, 1)

    class Config:
        """Model configuration."""
        from_attributes = True
        populate_by_name = True
        allow_population_by_field_name = True
        json_encoders = {
            TrendData: lambda v: v.dict()
        }

class PopularOpeningStats(BaseModel):
    """Statistics for popular openings"""
    name: str = Field(..., description="Full opening name")
    total_games: int = Field(..., description="Total number of games")
    white_win_rate: float = Field(..., description="Win rate for white")
    unique_players: int = Field(..., description="Number of unique players")
    variations: List[OpeningVariationStats] = Field(default_factory=list, description="List of variations within this opening")
