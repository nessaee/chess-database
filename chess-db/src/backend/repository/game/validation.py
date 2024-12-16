# repository/game/validation.py
from typing import Dict, Any, Optional
from datetime import datetime
import chess

from ..common.errors import ValidationError
from .types import GameData

class GameDataValidator:
    """
    Validator for chess game data with comprehensive validation rules.
    
    Handles validation of game data including:
    - Move validation
    - Result validation
    - Rating validation
    - Date validation
    - ECO code validation
    """
    
    VALID_RESULTS = {'1-0', '0-1', '1/2-1/2', '*'}
    
    def __init__(self):
        self._board = chess.Board()
    
    def validate_game_data(self, data: Dict[str, Any]) -> GameData:
        """
        Validate complete game data before storage.
        
        Args:
            data: Game data to validate
            
        Returns:
            Validated GameData object
            
        Raises:
            ValidationError: If validation fails
        """
        errors = []
        
        # Validate required fields
        required_fields = ['white_player_id', 'black_player_id', 'result', 'moves']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            raise ValidationError("Validation failed", errors=errors)
            
        # Validate player IDs
        if data['white_player_id'] == data['black_player_id']:
            errors.append("White and black player IDs cannot be the same")
            
        # Validate result
        if data['result'] not in self.VALID_RESULTS:
            errors.append(f"Invalid result: {data['result']}")
            
        # Validate moves
        if not self._validate_moves(data['moves']):
            errors.append("Invalid move sequence")
            
        # Validate ratings if present
        if 'white_elo' in data:
            self._validate_rating(data['white_elo'], 'white_elo', errors)
        if 'black_elo' in data:
            self._validate_rating(data['black_elo'], 'black_elo', errors)
            
        # Validate date if present
        if 'date' in data:
            self._validate_date(data['date'], errors)
            
        # Validate ECO code if present
        if 'eco' in data:
            self._validate_eco(data['eco'], errors)
            
        if errors:
            raise ValidationError("Validation failed", errors=errors)
            
        return GameData(**data)
    
    def _validate_moves(self, moves: str) -> bool:
        """Validate chess move sequence."""
        try:
            self._board.reset()
            for move in moves.split():
                self._board.push_uci(move)
            return True
        except ValueError:
            return False
            
    def _validate_rating(
        self,
        rating: Any,
        field: str,
        errors: list
    ) -> None:
        """Validate chess rating value."""
        try:
            rating_int = int(rating)
            if not (0 <= rating_int <= 3000):
                errors.append(f"{field} must be between 0 and 3000")
        except (TypeError, ValueError):
            errors.append(f"Invalid {field} value")
            
    def _validate_date(
        self,
        date: Any,
        errors: list
    ) -> None:
        """Validate game date."""
        if isinstance(date, str):
            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                errors.append("Invalid date format (use YYYY-MM-DD)")
                
    def _validate_eco(
        self,
        eco: str,
        errors: list
    ) -> None:
        """Validate ECO code format."""
        if not (
            len(eco) == 3 and
            eco[0] in 'ABCDE' and
            eco[1:].isdigit()
        ):
            errors.append("Invalid ECO code format")
