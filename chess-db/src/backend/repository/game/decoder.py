"""Game decoder for converting stored game data into usable format."""

import chess
import struct
import bitarray
from typing import List, Optional, Union, Tuple, Dict
import logging

logger = logging.getLogger(__name__)

class GameDecoder:
    """Decoder for chess game data."""

    def __init__(self):
        """Initialize decoder with move mapping."""
        self._square_names = chess.SQUARE_NAMES
        self._piece_symbols = {'p': 1, 'n': 2, 'b': 3, 'r': 4, 'q': 5}
        self._reverse_piece_symbols = {v: k for k, v in self._piece_symbols.items()}
        self._board = chess.Board()

    def decode_moves(self, encoded_data: bytes) -> List[str]:
        """
        Decode binary data back into a list of UCI moves.
        
        Args:
            encoded_data: Binary encoded moves
            
        Returns:
            List of moves in UCI format
            
        Raises:
            ValueError: If data format is invalid
        """
        if len(encoded_data) < 2:  # Minimum size for move count
            raise ValueError("Encoded data too short")

        bits = bitarray.bitarray()
        bits.frombytes(encoded_data)

        try:
            # Read move count
            move_count = struct.unpack('>H', bits[0:16].tobytes())[0]
            offset = 16

            # Validate expected data length
            expected_bits = 16 + (move_count * 16)
            if len(bits) < expected_bits:
                raise ValueError(
                    f"Encoded data too short for {move_count} moves. "
                    f"Expected {expected_bits} bits, got {len(bits)}"
                )

            # Decode moves
            moves = []
            for _ in range(move_count):
                encoded_move = struct.unpack(
                    '>H', 
                    bits[offset:offset + 16].tobytes()
                )[0]
                moves.append(self._decode_single_move(encoded_move))
                offset += 16

            return moves

        except (struct.error, ValueError) as e:
            raise ValueError(f"Failed to decode moves: {str(e)}") from e
        
    def _decode_single_move(self, encoded_move: int) -> str:
        """
        Decode a 16-bit integer back into a UCI move.
        
        Args:
            encoded_move: 16-bit integer representing the encoded move
            
        Returns:
            Move in UCI format
            
        Raises:
            ValueError: If encoded move is invalid
        """
        if not hasattr(self, '_reverse_cache'):
            self._reverse_cache = {}
        if encoded_move in self._reverse_cache:
            return self._reverse_cache[encoded_move]

        if not (0 <= encoded_move < 65536):  # 2^16
            raise ValueError(f"Invalid encoded move value: {encoded_move}")

        from_square = (encoded_move >> 10) & 0x3F
        to_square = (encoded_move >> 4) & 0x3F
        promotion = encoded_move & 0xF

        if from_square >= 64 or to_square >= 64:
            raise ValueError(f"Invalid square index in encoded move: {encoded_move}")

        move = chess.SQUARE_NAMES[from_square] + chess.SQUARE_NAMES[to_square]
        if promotion:
            if promotion > 6:
                raise ValueError(f"Invalid promotion value in encoded move: {encoded_move}")
            move += "pnbrqk"[promotion - 1]

        self._reverse_cache[encoded_move] = move
        return move

    def convert_uci_to_san(self, moves: Union[str, List[str]]) -> Tuple[List[str], Optional[str], int]:
        """
        Convert UCI moves to SAN notation and return additional game info.
        
        Args:
            moves: Either a space-separated string of UCI moves or a list of UCI moves
            
        Returns:
            Tuple containing:
            - List of moves in SAN format
            - Opening name (if available)
            - Number of moves
        """
        if not moves:
            return [], None, 0

        try:
            # Reset board
            self._board.reset()
            
            # Convert string to list if needed
            if isinstance(moves, str):
                uci_moves = moves.strip().split()
            else:
                uci_moves = moves

            # Convert moves
            san_moves = []
            for uci_move in uci_moves:
                try:
                    # Parse UCI move
                    move = chess.Move.from_uci(uci_move)
                    
                    # Convert to SAN and make move
                    san = self._board.san(move)
                    self._board.push(move)
                    san_moves.append(san)
                    
                except ValueError as e:
                    logger.error(f"Invalid UCI move {uci_move}: {str(e)}")
                    continue

            # Get opening name if available
            opening_name = self._get_opening_name(uci_moves[:10])

            return san_moves, opening_name, len(san_moves)

        except Exception as e:
            logger.error(f"Error converting UCI to SAN: {str(e)}")
            return [], None, 0

    def _get_opening_name(self, moves: List[str]) -> Optional[str]:
        """
        Get opening name based on initial moves.
        Currently returns None as opening book integration is not implemented.
        """
        return None