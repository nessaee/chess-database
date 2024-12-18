"""Database models for chess games."""

from .base import (
    Base, Column, Integer, String, Text, Date, SmallInteger,
    ForeignKey, relationship, BaseModel, ConfigDict
)
from .player import PlayerResponse, PlayerDB
from typing import Optional, Literal
from datetime import date

# Result mapping constants
RESULT_BLACK = 0   # '0-1'
RESULT_WHITE = 1   # '1-0'
RESULT_DRAW = 2    # '1/2-1/2'
RESULT_UNKNOWN = 3 # '*'

def decode_result(result_bits: int) -> str:
    """Convert 2-bit result to string representation."""
    result_map = {
        RESULT_BLACK: '0-1',
        RESULT_WHITE: '1-0',
        RESULT_DRAW: '1/2-1/2',
        RESULT_UNKNOWN: '*'
    }
    return result_map.get(result_bits, '*')

def encode_result(result_str: str) -> int:
    """Convert string result to 2-bit representation."""
    result_map = {
        '0-1': RESULT_BLACK,
        '1-0': RESULT_WHITE,
        '1/2-1/2': RESULT_DRAW,
        '*': RESULT_UNKNOWN
    }
    return result_map.get(result_str, RESULT_UNKNOWN)

class GameDB(Base):
    """Database model for chess games"""
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    white_player_id = Column(Integer, ForeignKey("players.id"))
    black_player_id = Column(Integer, ForeignKey("players.id"))
    white_elo = Column(SmallInteger, nullable=True)
    black_elo = Column(SmallInteger, nullable=True)
    date = Column(Date)
    result = Column(SmallInteger)  # 2-bit result stored as smallint
    eco = Column(String(3))
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

    def get_result_str(self) -> str:
        """Get the string representation of the result."""
        return decode_result(self.result)

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
    moves: Optional[str] = None
    num_moves: Optional[int] = None  # Total number of moves
    opening_name: Optional[str] = None  # ECO opening name if available

    @classmethod
    def from_db(cls, game: GameDB) -> "GameResponse":
        """Create response model from database model."""
        return cls(
            id=game.id,
            white_player_id=game.white_player_id,
            black_player_id=game.black_player_id,
            white_player=PlayerInGame(
                id=game.white_player.id,
                name=game.white_player.name,
                rating=game.white_elo
            ) if game.white_player else None,
            black_player=PlayerInGame(
                id=game.black_player.id,
                name=game.black_player.name,
                rating=game.black_elo
            ) if game.black_player else None,
            date=game.date,
            result=game.get_result_str(),
            eco=game.eco,
            moves=game.moves
        )

    model_config = ConfigDict(from_attributes=True)
