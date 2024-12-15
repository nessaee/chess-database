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




from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class OpeningAnalysis(BaseModel):
    """Analysis of a player's performance with a specific opening"""
    eco_code: str = Field(..., description="ECO code of the opening")
    games_played: int = Field(..., description="Number of games with this opening")
    wins: int = Field(..., description="Number of wins with this opening")
    draws: int = Field(..., description="Number of draws with this opening")
    win_rate: float = Field(..., description="Win percentage with this opening")
    performance_score: float = Field(..., description="Overall performance score")
    avg_moves: float = Field(..., description="Average game length with this opening")
    played_white: bool = Field(..., description="Has played this opening as white")
    played_black: bool = Field(..., description="Has played this opening as black")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "eco_code": "B07",
                "games_played": 42,
                "wins": 25,
                "draws": 10,
                "win_rate": 59.52,
                "performance_score": 71.43,
                "avg_moves": 35.8,
                "played_white": True,
                "played_black": True
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