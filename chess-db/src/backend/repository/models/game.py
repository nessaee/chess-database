"""Database models for chess games."""

from .base import (
    Base, Column, Integer, String, Text, Date,
    ForeignKey, relationship, BaseModel, ConfigDict
)
from .player import PlayerResponse, PlayerDB
from typing import Optional, List
from datetime import date

class GameDB(Base):
    """Database model for chess games"""
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    white_player_id = Column(Integer, ForeignKey("players.id"))
    black_player_id = Column(Integer, ForeignKey("players.id"))
    white_elo = Column(Integer, nullable=True)
    black_elo = Column(Integer, nullable=True)
    date = Column(Date)
    result = Column(String(10))
    eco = Column(String(10))
    moves = Column(Text)
    
    # Configure relationships with lazy="joined" for eager loading
    white_player = relationship(
        "PlayerDB",
        foreign_keys=[white_player_id],
        lazy="joined"
    )
    black_player = relationship(
        "PlayerDB",
        foreign_keys=[black_player_id],
        lazy="joined"
    )

class GameResponse(BaseModel):
    """API response model for chess games"""
    id: int
    white_player_id: int
    black_player_id: int
    white_player_name: Optional[str] = None
    black_player_name: Optional[str] = None
    date: Optional[date]
    result: str
    eco: Optional[str] = None
    moves: str  # Space-separated moves in requested notation (UCI or SAN)
    white_elo: Optional[int] = None
    black_elo: Optional[int] = None
    num_moves: Optional[int] = None  # Total number of moves
    opening_name: Optional[str] = None  # ECO opening name if available
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "white_player_id": 1,
                "black_player_id": 2,
                "white_player_name": "Player 1",
                "black_player_name": "Player 2",
                "date": "2023-01-01",
                "result": "1-0",
                "eco": "B20",
                "moves": "e2e4 e7e5 g1f3",  # UCI format by default
                "white_elo": 2000,
                "black_elo": 1900,
                "num_moves": 3,
                "opening_name": "Sicilian Defense"
            }
        }
    )
