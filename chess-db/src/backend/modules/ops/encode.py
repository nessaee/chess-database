from typing import List, Optional, Dict
import chess
import struct
import bitarray
from dataclasses import dataclass

@dataclass
class EncodedMoves:
    """Container for encoded chess moves with metadata"""
    move_count: int  # Total number of moves
    raw_bytes: bytes  # Binary encoded moves
    size_bytes: int  # Size of encoded data

class ChessMoveEncoder:
    """
    Efficient chess move encoder that focuses solely on move encoding.
    Converts UCI moves to a compact binary format for storage.
    """
    def __init__(self):
        # Cache for frequently used move encodings
        self._move_cache: Dict[str, int] = {}
        self._reverse_cache: Dict[int, str] = {}

    def _encode_single_move(self, uci_move: str) -> int:
        """
        Encode a single UCI move into a 16-bit integer.
        
        Format:
        - From square: 6 bits (0-63)
        - To square: 6 bits (0-63)
        - Promotion piece: 4 bits (0-15, where 0 means no promotion)
        
        Args:
            uci_move: Move in UCI format (e.g., 'e2e4', 'd7d8q')
            
        Returns:
            16-bit integer encoding of the move
            
        Raises:
            ValueError: If move format is invalid
        """
        if uci_move in self._move_cache:
            return self._move_cache[uci_move]

        if not (4 <= len(uci_move) <= 5):
            raise ValueError(f"Invalid UCI move format: {uci_move}")

        try:
            from_square = chess.SQUARE_NAMES.index(uci_move[:2])
            to_square = chess.SQUARE_NAMES.index(uci_move[2:4])
        except ValueError as e:
            raise ValueError(f"Invalid square name in move {uci_move}") from e

        promotion = 0
        if len(uci_move) == 5:
            try:
                # Map promotion pieces: p(1), n(2), b(3), r(4), q(5), k(6)
                promotion = "pnbrqk".index(uci_move[4].lower()) + 1
            except ValueError as e:
                raise ValueError(f"Invalid promotion piece in move {uci_move}") from e

        # Combine bits: from_square (6) | to_square (6) | promotion (4)
        encoded = (from_square << 10) | (to_square << 4) | promotion

        # Cache the encoding
        self._move_cache[uci_move] = encoded
        self._reverse_cache[encoded] = uci_move

        return encoded

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

    def encode_moves(self, moves: List[str]) -> EncodedMoves:
        """
        Encode a list of UCI moves into a compact binary format.
        
        Format:
        - Move count: 16 bits
        - Moves: sequence of 16-bit integers
        
        Args:
            moves: List of moves in UCI format
            
        Returns:
            EncodedMoves object containing the encoded data
            
        Raises:
            ValueError: If any move is invalid
        """
        bits = bitarray.bitarray()

        # Store move count (16 bits)
        bits.frombytes(struct.pack('>H', len(moves)))

        # Encode each move
        for move in moves:
            try:
                encoded_move = self._encode_single_move(move)
                bits.frombytes(struct.pack('>H', encoded_move))
            except ValueError as e:
                raise ValueError(f"Failed to encode move {move}: {str(e)}") from e

        encoded_bytes = bits.tobytes()
        return encoded_bytes
        return EncodedMoves(
            move_count=len(moves),
            raw_bytes=encoded_bytes,
            size_bytes=len(encoded_bytes)
        )

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

    def validate_moves(self, moves: List[str]) -> bool:
        """
        Validate that all moves are in correct UCI format and could be legally encoded.
        
        Args:
            moves: List of moves to validate
            
        Returns:
            True if all moves are valid, False otherwise
        """
        try:
            board = chess.Board()
            for move in moves:
                if not (4 <= len(move) <= 5):
                    return False
                    
                # Validate square names
                from_square = move[:2]
                to_square = move[2:4]
                if from_square not in chess.SQUARE_NAMES or to_square not in chess.SQUARE_NAMES:
                    return False
                    
                # Validate promotion if present
                if len(move) == 5 and move[4].lower() not in 'pnbrqk':
                    return False
                    
                # Validate move is legal
                try:
                    chess_move = chess.Move.from_uci(move)
                    if not chess_move in board.legal_moves:
                        return False
                    board.push(chess_move)
                except ValueError:
                    return False
                    
            return True
            
        except Exception:
            return False