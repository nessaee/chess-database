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
from typing import List, Dict, Union, TypedDict, Optional, Any, Tuple
import logging
from datetime import datetime
from modules.ops.encode import ChessMoveEncoder
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
        self.decoder = ChessMoveEncoder()

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
        counter = 0 
        limit = 1
        for game in games:
            if counter >= 100:
                break
            try:
                # Decode binary game data
                moves = self.decoder.decode_moves(game.moves)
                # Convert moves if needed
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
                counter+=1
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
            moves = self.decoder.decode_moves(game.moves)
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
                moves = self.decoder.decode_moves(game.moves)
                
                if move_notation == 'san':
                    moves = self.decoder.convert_uci_to_san(moves)
                
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
    

from typing import List, Dict, Optional, TypedDict, Tuple
import logging
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from modules.ops.encode import ChessMoveEncoder

class MoveCountStats(TypedDict):
    """Type definition for move count statistics"""
    actual_full_moves: int           # Number of full moves in game
    number_of_games: int            # Count of games with this move count
    avg_bytes: float               # Average size of encoded game data
    results: str                   # Aggregated game results
    min_stored_count: Optional[int] # Minimum stored move count
    max_stored_count: Optional[int] # Maximum stored move count
    avg_stored_count: float        # Average stored move count

class AnalysisRepository:
    """Repository for analyzing chess game statistics with focus on move data analysis"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session
        
        Args:
            db (AsyncSession): Async SQLAlchemy session for database operations
        """
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.AnalysisRepository")
        self.move_encoder = ChessMoveEncoder()  # For decoding move data if needed

    async def get_move_count_distribution(self) -> List[MoveCountStats]:
        """
        Analyze the distribution of move counts across chess games.
        
        This method computes statistics about game lengths, considering both the
        actual encoded moves and the stored move count in the header.
        
        Returns:
            List[MoveCountStats]: Array of move count statistics
            
        Raises:
            SQLAlchemyError: On database operation failures
            ValueError: If data validation fails
        """
        try:
            # Define analysis query with explicit column types and data validation
            query = text("""
                WITH game_moves_analysis AS (
                    SELECT
                        -- Calculate actual moves from binary data length
                        -- Subtract header size (19 bytes) and divide remaining by 2 bytes per move
                        (octet_length(moves) - 19) / 2 as actual_full_moves,
                        
                        -- Extract stored move count from header (bytes 17-18)
                        get_byte(moves, 17) << 8 | get_byte(moves, 18) as stored_move_count,
                        
                        -- Game metadata
                        result,
                        octet_length(moves) as total_bytes
                        
                    FROM games
                    WHERE moves IS NOT NULL
                        AND octet_length(moves) >= 19  -- Ensure minimum header size
                )
                SELECT
                    actual_full_moves,
                    COUNT(*) as number_of_games,
                    ROUND(AVG(total_bytes)::numeric, 2) as avg_bytes,
                    string_agg(DISTINCT result, ', ' ORDER BY result) as results,
                    MIN(stored_move_count) as min_stored_count,
                    MAX(stored_move_count) as max_stored_count,
                    ROUND(AVG(stored_move_count)::numeric, 2) as avg_stored_count
                    
                FROM game_moves_analysis
                WHERE 
                    -- Filter out invalid move counts
                    actual_full_moves >= 0
                    AND actual_full_moves <= 500  -- Reasonable maximum game length
                    
                GROUP BY actual_full_moves
                ORDER BY actual_full_moves ASC;
            """)

            # Execute query with explicit transaction handling
            result = await self.db.execute(query)
            raw_rows = result.fetchall()

            # Process and validate results
            processed_results: List[MoveCountStats] = []
            
            for row in raw_rows:
                try:
                    # Validate numeric fields
                    actual_moves = int(row[0])
                    num_games = int(row[1])
                    avg_bytes = float(row[2])
                    min_count = int(row[4]) if row[4] is not None else None
                    max_count = int(row[5]) if row[5] is not None else None
                    avg_count = float(row[6]) if row[6] is not None else 0.0

                    # Validate value ranges
                    if not (0 <= actual_moves <= 500):
                        self.logger.warning(
                            f"Invalid move count detected: {actual_moves}"
                        )
                        continue

                    if num_games <= 0:
                        self.logger.warning(
                            f"Invalid game count: {num_games} for {actual_moves} moves"
                        )
                        continue

                    processed_row = MoveCountStats(
                        actual_full_moves=actual_moves,
                        number_of_games=num_games,
                        avg_bytes=avg_bytes,
                        results=str(row[3]),
                        min_stored_count=min_count,
                        max_stored_count=max_count,
                        avg_stored_count=avg_count
                    )
                    processed_results.append(processed_row)

                except (TypeError, ValueError) as e:
                    self.logger.warning(
                        f"Error processing row: {row}",
                        exc_info=e
                    )
                    continue

            # Validate final result set
            if not processed_results:
                self.logger.warning("No valid move count data found")
                return []

            return processed_results

        except SQLAlchemyError as e:
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