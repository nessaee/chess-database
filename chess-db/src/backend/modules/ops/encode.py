from dataclasses import dataclass
from datetime import datetime
import struct
import chess
import bitarray
from typing import Optional, Tuple, List, Dict, Any

@dataclass
class ChessGameMetadata:
    white_player_id: int
    black_player_id: int
    white_elo: int
    black_elo: int
    date: Optional[datetime]
    result: str
    eco: str
    moves: str

class ChessGameEncoder:
    # Mapping for chess results to 2-bit representation
    RESULT_ENCODING = {
        '1-0': 0b00,    # White wins
        '0-1': 0b01,    # Black wins
        '1/2-1/2': 0b10,  # Draw
        '*': 0b11      # Unknown/Ongoing
    }
    
    RESULT_DECODING = {v: k for k, v in RESULT_ENCODING.items()}
    
    def __init__(self):
        self.move_cache = {}
        self.reverse_move_cache = {}
        
    def _encode_move(self, uci_move: str) -> int:
        """
        Encodes a UCI move into a 16-bit integer:
        - From square: 6 bits (0-63)
        - To square: 6 bits (0-63)
        - Promotion piece: 4 bits (0-15, where 0 means no promotion)
        """
        if uci_move in self.move_cache:
            return self.move_cache[uci_move]
            
        from_square = chess.SQUARE_NAMES.index(uci_move[:2])
        to_square = chess.SQUARE_NAMES.index(uci_move[2:4])
        promotion = 0
        if len(uci_move) == 5:
            promotion = "pnbrqk".index(uci_move[4].lower()) + 1
            
        encoded = (from_square << 10) | (to_square << 4) | promotion
        self.move_cache[uci_move] = encoded
        self.reverse_move_cache[encoded] = uci_move
        return encoded

    def _decode_move(self, encoded_move: int) -> str:
        """Decodes a 16-bit integer back into a UCI move."""
        if encoded_move in self.reverse_move_cache:
            return self.reverse_move_cache[encoded_move]
            
        from_square = (encoded_move >> 10) & 0x3F
        to_square = (encoded_move >> 4) & 0x3F
        promotion = encoded_move & 0xF
        
        move = chess.SQUARE_NAMES[from_square] + chess.SQUARE_NAMES[to_square]
        if promotion:
            move += "pnbrqk"[promotion - 1]
            
        self.reverse_move_cache[encoded_move] = move
        return move

    def encode_game(self, game: ChessGameMetadata) -> bytes:
        """
        Encodes a chess game into a compressed binary format:
        - Player IDs: 4 bytes each (32-bit int)
        - ELO ratings: 2 bytes each (16-bit int)
        - Date: 3 bytes (year: 12 bits, month: 4 bits, day: 4 bits)
        - Result: 2 bits
        - ECO: 2 bytes (compressed character encoding)
        - Moves: variable length, each move 16 bits
        """
        # Create a bit array for efficient bit-level operations
        bits = bitarray.bitarray()
        
        # Encode player IDs and ELO ratings
        bits.frombytes(struct.pack('>II', game.white_player_id, game.black_player_id))
        bits.frombytes(struct.pack('>HH', game.white_elo, game.black_elo))
        
        # Encode date
        if game.date:
            year_bits = format(game.date.year - 1900, '012b')
            month_bits = format(game.date.month, '04b')
            day_bits = format(game.date.day, '04b')
        else:
            year_bits = '0' * 12
            month_bits = '0' * 4
            day_bits = '0' * 4
        bits.extend(map(int, year_bits + month_bits + day_bits))
        
        # Encode result (2 bits)
        result_bits = format(self.RESULT_ENCODING[game.result], '02b')
        bits.extend(map(int, result_bits))
        
        # Encode ECO (2 bytes)
        eco_num = (ord(game.eco[0]) - ord('A')) * 100 + int(game.eco[1:])
        bits.frombytes(struct.pack('>H', eco_num))
        
        # Encode moves
        moves = game.moves.split()
        bits.frombytes(struct.pack('>H', len(moves)))  # Number of moves (2 bytes)
        
        for move in moves:
            encoded_move = self._encode_move(move)
            bits.frombytes(struct.pack('>H', encoded_move))
        
        return bits.tobytes()

    def decode_game(self, binary_data: bytes) -> Dict[str, Any]:
        """
        Decode binary game data into a dictionary of game information with debug printing.
        
        Args:
            binary_data: Raw binary game data from database
            
        Returns:
            Dict containing decoded game information including moves
        """
        bits = bitarray.bitarray()
        bits.frombytes(binary_data)
        offset = 0
        
        # Debug print total length
        print(f"Total binary data length: {len(binary_data)} bytes")
        
        # Decode player IDs (32 bits each = 8 bytes total)
        print(f"Player IDs start at byte {offset//8}")
        white_id, black_id = struct.unpack('>II', bits[offset:offset+64].tobytes())
        print(f"White ID: {white_id}, Black ID: {black_id}")
        offset += 64  # Now at byte 8
        
        # Decode ELO ratings (16 bits each = 4 bytes total)
        print(f"ELO ratings start at byte {offset//8}")
        white_elo, black_elo = struct.unpack('>HH', bits[offset:offset+32].tobytes())
        print(f"White ELO: {white_elo}, Black ELO: {black_elo}")
        offset += 32  # Now at byte 12
        
        # Decode date (20 bits: year-12, month-4, day-4)
        print(f"Date starts at byte {offset//8}")
        year = int(bits[offset:offset+12].to01(), 2) + 1900
        month = int(bits[offset+12:offset+16].to01(), 2)
        day = int(bits[offset+16:offset+20].to01(), 2)
        print(f"Date components - Year: {year}, Month: {month}, Day: {day}")
        offset += 20  # Now at bit 148 (byte 18 + 4 bits)
        
        # Decode result (2 bits)
        print(f"Result starts at bit {offset}")
        result_val = int(bits[offset:offset+2].to01(), 2)
        result = self.RESULT_DECODING.get(result_val, '*')
        print(f"Result value: {result_val} -> {result}")
        offset += 2  # Now at bit 150 (byte 18 + 6 bits)
        
        # Decode ECO code (16 bits = 2 bytes)
        print(f"ECO starts at bit {offset} (byte {offset//8})")
        eco_num = struct.unpack('>H', bits[offset:offset+16].tobytes())[0]
        eco = chr(ord('A') + eco_num // 100) + str(eco_num % 100).zfill(2)
        print(f"ECO: {eco}")
        offset += 16  # Now at byte 21
        
        # Decode move count (16 bits = 2 bytes)
        print(f"Move count starts at byte {offset//8}")
        num_moves = struct.unpack('>H', bits[offset:offset+16].tobytes())[0]
        print(f"Number of moves: {num_moves}")
        offset += 16  # Now at byte 23
        
        # Verify our earlier calculation - moves should start at byte 19
        print(f"\nMove data starts at byte {offset//8}")
        print(f"Expected move start at byte 19")
        print(f"Difference from expected: {offset//8 - 19} bytes")
        
        moves = []
        for i in range(num_moves):
            encoded_move = struct.unpack('>H', bits[offset:offset+16].tobytes())[0]
            move = self._decode_move(encoded_move)
            moves.append(move)
            print(f"Move {i+1}: {move} (bytes {offset//8}-{(offset+16)//8})")
            offset += 16

        return {
            'white_player_id': white_id,
            'black_player_id': black_id,
            'white_elo': white_elo,
            'black_elo': black_elo,
            'date': datetime(year, month, day).date() if all([year != 1900, month != 0, day != 0]) else None,
            'result': result,
            'eco': eco,
            'moves': moves
        }
    
    def estimate_compression_ratio(self, game: ChessGameMetadata) -> float:
        """Estimates the compression ratio achieved by the binary encoding."""
        original_size = (
            8 +  # player IDs (4 bytes each)
            4 +  # ELO ratings (2 bytes each)
            10 + # date string (YYYY.MM.DD)
            7 +  # result string (max length)
            3 +  # ECO
            len(game.moves)  # moves string
        )
        
        compressed_size = len(self.encode_game(game))
        return original_size / compressed_size