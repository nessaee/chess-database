from sqlalchemy.orm import Session,joinedload
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from models import ItemDB, ItemCreate, ItemUpdate
from models import GameDB, PlayerDB 
from datetime import datetime
from typing import List, Optional, Dict, Any
import chess
import bitarray
import struct
from models import GameDB, PlayerDB, GameResponse
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result
from typing import List, Dict, Union, TypedDict, Optional
import logging
from datetime import datetime

class ItemRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_item(self, item: ItemCreate) -> ItemDB:
        db_item = ItemDB(**item.model_dump())
        self.db.add(db_item)
        await self.db.commit()
        await self.db.refresh(db_item)
        return db_item

    async def get_items(self) -> list[ItemDB]:
        result = await self.db.execute(select(ItemDB))
        return result.scalars().all()

    async def get_item(self, item_id: int) -> ItemDB | None:
        result = await self.db.execute(select(ItemDB).filter(ItemDB.id == item_id))
        return result.scalar_one_or_none()

    async def update_item(self, item_id: int, item: ItemUpdate) -> ItemDB | None:
        db_item = await self.get_item(item_id)
        if not db_item:
            return None
            
        update_data = item.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_item, key, value)
            
        await self.db.commit()
        await self.db.refresh(db_item)
        return db_item

    async def delete_item(self, item_id: int) -> bool:
        db_item = await self.get_item(item_id)
        if not db_item:
            return False
            
        await self.db.delete(db_item)
        await self.db.commit()
        return True
    

class ChessGameDecoder:
    """
    Handles decoding of binary-encoded chess game data and move format conversion.
    """
    
    # Mapping for chess results from 2-bit representation
    RESULT_DECODING = {
        0b00: '1-0',     # White wins
        0b01: '0-1',     # Black wins
        0b10: '1/2-1/2', # Draw
        0b11: '*'        # Unknown/Ongoing
    }
    
    def __init__(self):
        """Initialize decoder with move conversion caches."""
        self.move_cache = {}
        self.reverse_move_cache = {}

    def _decode_move(self, encoded_move: int) -> str:
        """
        Decode a 16-bit integer into a UCI move string.
        
        Args:
            encoded_move: Integer representing encoded chess move
            
        Returns:
            str: UCI format move (e.g., 'e2e4')
        """
        if encoded_move in self.reverse_move_cache:
            return self.reverse_move_cache[encoded_move]
        
        print(bin(encoded_move))
        from_square = (encoded_move >> 10) & 0x3F
        to_square = (encoded_move >> 4) & 0x3F
        promotion = encoded_move & 0xF
        # trim last digit of promotion
        
        # binary promotion: 0001 -> 1, 0010 -> 2, 0011 -> 3, 0100 -> 4, 0101 -> 5
        print(bin(promotion))
        
        move = chess.SQUARE_NAMES[from_square] + chess.SQUARE_NAMES[to_square]
        if promotion:
            print(f"from_square: {from_square}, to_square: {to_square}, promotion: {promotion}")
            print(f"Promotion: {promotion}")
            move += "pnbrqk"[promotion - 1]
            
        self.reverse_move_cache[encoded_move] = move
        return move

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
    

    def convert_uci_to_san(self, uci_moves: List[str]) -> List[str]:
        """
        Convert a list of UCI moves to Standard Algebraic Notation (SAN).
        
        Args:
            uci_moves: List of moves in UCI format (e.g., ['e2e4', 'e7e5'])
            
        Returns:
            List of moves in SAN format (e.g., ['e4', 'e5'])
        """
        board = chess.Board()
        san_moves = []
        
        for uci_move in uci_moves:
            try:
                move = chess.Move.from_uci(uci_move)
                san_moves.append(board.san(move))
                board.push(move)
            except (chess.InvalidMoveError, chess.IllegalMoveError) as e:
                # Log error but continue processing remaining moves
                print(f"Error converting move {uci_move}: {str(e)}")
                san_moves.append(uci_move)  # Fall back to UCI notation
                
        return san_moves

class GameRepository:
    """
    Enhanced repository layer for chess game data with move format conversion.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session and decoder.
        
        Args:
            db: Asynchronous database session
        """
        self.db = db
        self.decoder = ChessGameDecoder()

    async def get_games(
        self,
        player_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
        move_notation: str = 'uci'  # Options: 'uci' or 'san'
    ) -> List[GameResponse]:
        """
        Retrieve games with optional filtering and move notation conversion.
        
        Args:
            player_name: Filter by player name (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            limit: Maximum number of games to return
            move_notation: Desired move notation format ('uci' or 'san')
            
        Returns:
            List of GameResponse objects with decoded moves
        """
        # Construct base query
        query = (
            select(GameDB)
            .options(
                joinedload(GameDB.white_player),
                joinedload(GameDB.black_player)
            )
        )

        query = query.where(GameDB.date.isnot(None))
        
        # Apply filters
        if player_name:
            player_filter = or_(
                GameDB.white_player.has(
                    PlayerDB.name.ilike(f'%{player_name}%')
                ),
                GameDB.black_player.has(
                    PlayerDB.name.ilike(f'%{player_name}%')
                )
            )
            query = query.where(player_filter)

        if start_date:
            query = query.where(GameDB.date >= start_date)
        
        if end_date:
            query = query.where(GameDB.date <= end_date)

        # Apply limit and ordering
        query = query.order_by(GameDB.date.desc()).limit(limit)
        
        # Execute query
        result = await self.db.execute(query)
        games = result.scalars().unique().all()
        # Process games and convert moves
        processed_games = []
        for game in games:
            try:
                # Decode binary game data
                decoded_data = self.decoder.decode_game(game.moves)

                # Convert moves if needed
                moves = decoded_data['moves']
                if move_notation == 'san':
                    moves = self.decoder.convert_uci_to_san(moves)
                
                # Create response object
                processed_game = GameResponse(
                    id=game.id,
                    white_player_id=game.white_player_id,
                    black_player_id=game.black_player_id,
                    white_player=game.white_player,
                    black_player=game.black_player,
                    date=game.date,
                    result=game.result,
                    eco=game.eco,
                    moves=' '.join(moves)
                )
                processed_games.append(processed_game)
                
            except Exception as e:
                # Log error but continue processing other games
                print(f"Error processing game {game.id}: {str(e)}")
                continue
        
        return processed_games

    async def get_game(self, game_id: int, move_notation: str = 'san') -> Optional[GameResponse]:
        """
        Retrieve a single game by ID with move notation conversion.
        
        Args:
            game_id: ID of the game to retrieve
            move_notation: Desired move notation format ('uci' or 'san')
            
        Returns:
            GameResponse object if found, None otherwise
        """
        result = await self.db.execute(
            select(GameDB)
            .options(
                joinedload(GameDB.white_player),
                joinedload(GameDB.black_player)
            )
            .filter(GameDB.id == game_id)
        )
        
        game = result.scalar_one_or_none()
        if not game:
            return None
            
        try:
            # Decode binary game data
            decoded_data = self.decoder.decode_game(game.moves)
            
            # Convert moves if needed
            moves = decoded_data['moves']
            if move_notation == 'san':
                moves = self.decoder.convert_uci_to_san(moves)
            
            return GameResponse(
                id=game.id,
                white_player_id=game.white_player_id,
                black_player_id=game.black_player_id,
                white_player=game.white_player,
                black_player=game.black_player,
                date=game.date,
                result=game.result,
                eco=game.eco,
                moves=' '.join(moves)
            )
            
        except Exception as e:
            print(f"Error processing game {game_id}: {str(e)}")
            return None

    async def get_player_games(
        self,
        player_id: int,
        move_notation: str = 'san'
    ) -> List[GameResponse]:
        """
        Retrieve all games for a specific player.
        
        Args:
            player_id: ID of the player
            move_notation: Desired move notation format ('uci' or 'san')
            
        Returns:
            List of GameResponse objects for the player
        """
        result = await self.db.execute(
            select(GameDB)
            .options(
                joinedload(GameDB.white_player),
                joinedload(GameDB.black_player)
            )
            .where(
                or_(
                    GameDB.white_player_id == player_id,
                    GameDB.black_player_id == player_id
                )
            )
            .order_by(GameDB.date.desc())
        )
        
        games = result.scalars().unique().all()
        
        processed_games = []
        for game in games:
            try:
                decoded_data = self.decoder.decode_game(game.moves)
                moves = decoded_data['moves']
                
                if move_notation == 'san':
                    moves = self.decoder.convert_uci_to_san(moves)
                
                processed_game = GameResponse(
                    id=game.id,
                    white_player_id=decoded_data['white_player_id'],
                    black_player_id=decoded_data['black_player_id'],
                    white_player=game.white_player,
                    black_player=game.black_player,
                    date=decoded_data['date'],
                    result=decoded_data['result'],
                    eco=decoded_data['eco'],
                    moves=' '.join(moves)
                )
                processed_games.append(processed_game)
                
            except Exception as e:
                print(f"Error processing game {game.id}: {str(e)}")
                continue
                
        return processed_games

    async def get_game_stats(self):
        # Get basic statistics about the games
        result = await self.db.execute("""
            SELECT 
                COUNT(*) as total_games,
                COUNT(DISTINCT white_player_id) + COUNT(DISTINCT black_player_id) as total_players,
                MIN(date) as earliest_game,
                MAX(date) as latest_game
            FROM games
        """)
        stats = await result.first()
        return {
            "total_games": stats[0],
            "total_players": stats[1],
            "earliest_game": stats[2],
            "latest_game": stats[3]
        }
    

class MoveCountStats(TypedDict):
    """Type definition for move count statistics"""
    actual_full_moves: int
    number_of_games: int
    avg_bytes: float
    results: str
    min_stored_count: Optional[int]
    max_stored_count: Optional[int]
    avg_stored_count: float

class AnalysisRepository:
    """Repository for analyzing chess game statistics with async SQL operations"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize repository with async database session
        
        Args:
            db (AsyncSession): Async SQLAlchemy session for database operations
        """
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.AnalysisRepository")

    async def get_move_count_distribution(self) -> List[MoveCountStats]:
        """
        Analyze the distribution of move counts across chess games
        
        Returns:
            List[MoveCountStats]: Array of move count statistics
            
        Raises:
            ValueError: If data validation fails or processing errors occur
            SQLAlchemyError: On database operation failures
        """
        try:
            # Define analysis query with explicit column types
            query = text("""
                WITH game_moves_analysis AS (
                    SELECT
                        (length(moves) - 20) / 4 as actual_full_moves,
                        result,
                        (get_byte(moves, 17) << 8 | get_byte(moves, 18)) as stored_move_count,
                        length(moves) as total_bytes
                    FROM games
                    WHERE moves IS NOT NULL
                )
                SELECT
                    CAST(actual_full_moves AS INTEGER) as actual_full_moves,
                    CAST(COUNT(*) AS INTEGER) as number_of_games,
                    ROUND(CAST(AVG(total_bytes) AS NUMERIC), 2) as avg_bytes,
                    string_agg(DISTINCT result, ', ' ORDER BY result) as results,
                    MIN(stored_move_count) as min_stored_count,
                    MAX(stored_move_count) as max_stored_count,
                    ROUND(CAST(AVG(stored_move_count) AS NUMERIC), 2) as avg_stored_count
                FROM game_moves_analysis
                WHERE actual_full_moves >= 0
                GROUP BY actual_full_moves
                ORDER BY actual_full_moves ASC;
            """)

            # Execute query with explicit transaction handling
            result: Result = await self.db.execute(query)
            
            # Process results with validation
            processed_results: List[MoveCountStats] = []
            
            # Use fetchall() without await as it's already a list
            raw_rows = result.fetchall()
            
            for row in raw_rows:
                try:
                    # Convert and validate each field
                    processed_row = MoveCountStats(
                        actual_full_moves=int(row[0]),
                        number_of_games=int(row[1]),
                        avg_bytes=float(row[2]),
                        results=str(row[3]),
                        min_stored_count=int(row[4]) if row[4] is not None else None,
                        max_stored_count=int(row[5]) if row[5] is not None else None,
                        avg_stored_count=float(row[6]) if row[6] is not None else 0.0
                    )
                    
                    # Validate value ranges
                    if not 0 <= processed_row["actual_full_moves"] <= 500:
                        self.logger.warning(f"Invalid move count: {processed_row['actual_full_moves']}")
                        continue
                        
                    if processed_row["number_of_games"] <= 0:
                        self.logger.warning(f"Invalid game count: {processed_row['number_of_games']}")
                        continue
                        
                    processed_results.append(processed_row)
                    
                except (TypeError, ValueError) as e:
                    self.logger.warning(f"Error processing row: {row}", exc_info=e)
                    continue

            # Validate final result set
            if not processed_results:
                self.logger.warning("No valid move count data found")
                return []
                
            return processed_results
            
        except Exception as e:
            error_time = datetime.utcnow().isoformat()
            self.logger.error(
                "Move count analysis failed",
                extra={
                    "timestamp": error_time,
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"Error analyzing move count distribution: {str(e)}")
        