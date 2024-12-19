"""Database models for chess games."""

from .base import (
    Base, Column, Integer, String, Text, Date, SmallInteger,
    ForeignKey, relationship, BaseModel, ConfigDict
)
from .player import PlayerResponse, PlayerDB
from typing import Optional, Literal, List
from datetime import date
import logging

logger = logging.getLogger(__name__)

# Result mapping constants
RESULT_UNKNOWN = 3  # '*'
RESULT_DRAW = 2     # '1/2-1/2'
RESULT_WHITE = 1   # '1-0'
RESULT_BLACK = 0    # '0-1'

def decode_result(result_bits: int) -> str:
    """Convert 2-bit result to string representation."""
    result_map = {
        RESULT_UNKNOWN: '*',
        RESULT_DRAW: '1/2-1/2',
        RESULT_WHITE: '1-0',
        RESULT_BLACK: '0-1'
    }
    return result_map.get(result_bits, '*')

def encode_result(result_str: str) -> int:
    """Convert string result to 2-bit representation."""
    result_map = {
        '*': RESULT_UNKNOWN,
        '1/2-1/2': RESULT_DRAW,
        '1-0': RESULT_WHITE,
        '0-1': RESULT_BLACK
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

    @classmethod
    def from_result_str(cls, result_str: str) -> int:
        """Convert string result to database format."""
        return encode_result(result_str)

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
    moves: Optional[List[str]] = None  # List of moves in UCI format
    moves_san: Optional[List[str]] = None  # List of moves in SAN format
    num_moves: Optional[int] = None  # Total number of moves
    opening_name: Optional[str] = None  # ECO opening name if available

    @classmethod
    def from_db(cls, game: GameDB, move_notation: str = 'uci') -> "GameResponse":
        """Create response model from database model."""
        from ..game.decoder import GameDecoder
        decoder = GameDecoder()

        # Decode moves if present
        moves = None
        moves_san = None
        num_moves = None
        if game.moves:
            try:
                moves = decoder.decode_moves(game.moves)
                num_moves = len(moves)
                if move_notation == 'san':
                    moves_san = decoder.convert_to_san(moves)
            except Exception as e:
                logger.error(f"Failed to decode moves for game {game.id}: {str(e)}")
                moves = None
                moves_san = None
                num_moves = None

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
            moves=moves_san if move_notation == 'san' else moves,
            moves_san=moves_san,
            num_moves=num_moves,
            opening_name=None  # To be populated later if needed
        )

    model_config = ConfigDict(from_attributes=True)
