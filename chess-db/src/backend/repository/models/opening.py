"""
Models for opening analysis using the game_opening_matches materialized view.
"""

from datetime import date, timedelta
from typing import Optional, List, Dict, Any, Union
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

class OpeningComplexityStats(BaseModel):
    """Statistics for opening complexity and timing"""
    avg_time_per_move: Optional[timedelta] = Field(None, description="Average time spent per move")
    complexity_score: Optional[float] = Field(None, description="Calculated complexity score (0-1)")

    class Config:
        """Model configuration."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "avg_time_per_move": "00:00:30",
                "complexity_score": 0.75
            }
        }

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
        except (json.JSONDecodeError, TypeError, ValueError):
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
    eco_code: str = Field(..., description="ECO code")
    total_games: int = Field(..., description="Total number of games")
    wins: int = Field(..., description="Number of wins")
    draws: int = Field(..., description="Number of draws")
    losses: int = Field(..., description="Number of losses")
    win_rate: float = Field(..., description="Win rate percentage")
    games_as_white: int = Field(..., description="Games played as white")
    games_as_black: int = Field(..., description="Games played as black")
    avg_game_length: float = Field(..., description="Average game length in moves")
    last_played: date = Field(..., description="Date of last game")
    trend_data: Union[str, TrendData] = Field(default_factory=TrendData, description="Monthly trend data")
    variations: List[Dict[str, Any]] = Field(default_factory=list, description="List of variations")
    complexity_stats: OpeningComplexityStats = Field(
        default_factory=OpeningComplexityStats,
        description="Complexity and timing statistics"
    )
    popularity_score: Optional[int] = Field(None, description="Overall popularity score")

    def __init__(self, **data):
        """Initialize OpeningStats with custom handling for trend_data."""
        if "trend_data" in data and isinstance(data["trend_data"], str):
            data["trend_data"] = TrendData.from_json(data["trend_data"])
        if "complexity_stats" in data and isinstance(data["complexity_stats"], dict):
            data["complexity_stats"] = OpeningComplexityStats(**data["complexity_stats"])
        super().__init__(**data)

    class Config:
        """Model configuration."""
        from_attributes = True
        populate_by_name = True
        allow_population_by_field_name = True
        json_encoders = {
            TrendData: lambda v: v.dict(),
            OpeningComplexityStats: lambda v: v.dict()
        }

    @property
    def draw_rate(self) -> float:
        """Calculate draw rate."""
        return (self.draws / self.total_games * 100) if self.total_games > 0 else 0.0

    @property
    def loss_rate(self) -> float:
        """Calculate loss rate."""
        return (self.losses / self.total_games * 100) if self.total_games > 0 else 0.0

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
    eco_code: str = Field(..., description="ECO code")
    total_games: int = Field(..., description="Total number of games")
    unique_players: int = Field(..., description="Number of unique players")
    avg_game_length: float = Field(..., description="Average game length in moves")
    avg_opening_length: float = Field(..., description="Average opening length in moves")
    complexity_score: Optional[float] = Field(None, description="Opening complexity score")
    popularity_score: Optional[int] = Field(None, description="Overall popularity score")
    variations: List[Dict[str, Any]] = Field(default_factory=list, description="List of variations")
    white_win_rate: float = Field(..., description="Win rate for white")
    draw_rate: float = Field(..., description="Draw rate percentage")
    recent_analysis: Optional[List[Dict[str, Any]]] = Field(None, description="Recent engine analysis results")
