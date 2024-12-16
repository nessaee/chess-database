# repository/game/types.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class GameFilters(BaseModel):
    """Filter parameters for game queries."""
    player_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    min_rating: Optional[int] = Field(None, ge=0, le=3000)
    eco: Optional[str] = Field(None, regex="^[A-E][0-9]{2}$")
    
    def validate(self):
        """Validate filter parameters."""
        # Validate dates if provided
        if self.start_date:
            try:
                datetime.strptime(self.start_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Invalid start_date format (YYYY-MM-DD)")
                
        if self.end_date:
            try:
                datetime.strptime(self.end_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Invalid end_date format (YYYY-MM-DD)")
                
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date cannot be after end_date")

@dataclass
class GameData:
    """Chess game data structure."""
    id: int
    white_player_id: int
    black_player_id: int
    white_player_name: str
    black_player_name: str
    date: Optional[datetime]
    result: str
    eco: Optional[str]
    moves: str
    white_elo: Optional[int]
    black_elo: Optional[int]
    
    @classmethod
    def from_row(cls, row) -> 'GameData':
        """Create GameData from database row."""
        return cls(
            id=row[0],
            white_player_id=row[1],
            black_player_id=row[2],
            white_player_name=row[3],
            black_player_name=row[4],
            date=row[5],
            result=row[6],
            eco=row[7],
            moves=row[8],
            white_elo=row[9],
            black_elo=row[10]
        )

@dataclass
class GameStats:
    """Game statistics summary."""
    total_games: int
    total_players: int
    avg_game_length: float
    eco_distribution: Dict[str, int]
    rating_distribution: Dict[str, int]
    result_distribution: Dict[str, int]
    date_range: tuple[datetime, datetime]
    
    @classmethod
    def from_row(cls, row) -> 'GameStats':
        """Create GameStats from database row."""
        return cls(
            total_games=row[0],
            total_players=row[1],
            avg_game_length=row[2],
            eco_distribution=row[3],
            rating_distribution=row[4],
            result_distribution=row[5],
            date_range=(row[6], row[7])
        )