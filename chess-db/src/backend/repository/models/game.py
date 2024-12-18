"""Database models for chess games."""

from .base import (
    Base, Column, Integer, String, Text, Date,
    ForeignKey, relationship, BaseModel, ConfigDict
)
from .player import PlayerResponse, PlayerDB
from typing import Optional
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

class PlayerInGame(BaseModel):
    """Player information within a game response"""
    id: int
    name: str
    rating: Optional[int] = None

class GameResponse(BaseModel):
    """API response model for chess games"""
    id: int
    white_player_id: int
    black_player_id: int
    white_player: Optional[PlayerInGame] = None
    black_player: Optional[PlayerInGame] = None
    date: Optional[date]
    result: str
    eco: Optional[str] = None
    moves: str  # Space-separated moves in requested notation (UCI or SAN)
    num_moves: Optional[int] = None  # Total number of moves
    opening_name: Optional[str] = None  # ECO opening name if available

    model_config = ConfigDict(from_attributes=True)
