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
from models import GameDB, PlayerDB, GameResponse, PlayerResponse, OpeningAnalysis, OpeningAnalysisResponse
import logging
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Result
from typing import List, Dict, Union, TypedDict, Optional, Any, Tuple
import logging
from datetime import datetime
from backend.utils.encode import ChessMoveEncoder

from datetime import datetime
from typing import Optional, Tuple
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging

class DateValidationError(ValueError):
    """Custom exception for date validation errors."""
    pass

class DateHandler:
    """Utility class for handling date validation and conversion in chess analysis."""
    
    # Regular expression for validating ISO date format (YYYY-MM-DD)
    ISO_DATE_PATTERN = re.compile(r'^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$')
    
    @staticmethod
    def validate_and_parse_date(date_str: Optional[str], param_name: str) -> Optional[str]:
        """
        Validates and parses a date string into PostgreSQL-compatible format.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            param_name: Name of the parameter for error messages
            
        Returns:
            Optional[str]: Validated date string in PostgreSQL format
            
        Raises:
            DateValidationError: If date format is invalid or date is not logical
        """
        if not date_str:
            return None
            
        # Validate format using regex
        if not DateHandler.ISO_DATE_PATTERN.match(date_str):
            raise DateValidationError(
                f"Invalid date format for {param_name}. "
                f"Expected YYYY-MM-DD, got: {date_str}"
            )
            
        try:
            # Parse date to validate logical date values
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Validate year is within reasonable range
            current_year = datetime.now().year
            if not (1800 <= date_obj.year <= current_year + 1):
                raise DateValidationError(
                    f"Year in {param_name} must be between 1800 and {current_year + 1}"
                )
            
            # Return date in PostgreSQL-compatible format
            return date_obj.strftime('%Y-%m-%d')
            
        except ValueError as e:
            raise DateValidationError(
                f"Invalid date value for {param_name}: {str(e)}"
            )

    @staticmethod
    def validate_date_range(
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Validates a date range, ensuring start date is before or equal to end date.
        
        Args:
            start_date: Start date string in YYYY-MM-DD format
            end_date: End date string in YYYY-MM-DD format
            
        Returns:
            Tuple[Optional[str], Optional[str]]: Validated start and end dates
            
        Raises:
            DateValidationError: If date range is invalid
        """
        # Parse both dates
        parsed_start = DateHandler.validate_and_parse_date(
            start_date, "start_date"
        ) if start_date else None
        parsed_end = DateHandler.validate_and_parse_date(
            end_date, "end_date"
        ) if end_date else None
        
        # Validate range if both dates are provided
        if parsed_start and parsed_end:
            start_obj = datetime.strptime(parsed_start, '%Y-%m-%d')
            end_obj = datetime.strptime(parsed_end, '%Y-%m-%d')
            
            if start_obj > end_obj:
                raise DateValidationError(
                    f"Start date ({parsed_start}) must not be after "
                    f"end date ({parsed_end})"
                )
        
        return parsed_start, parsed_end
    
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
from backend.utils.encode import ChessMoveEncoder

class MoveCountStats(TypedDict):
    """Type definition for move count statistics"""
    actual_full_moves: int           # Number of full moves in game
    number_of_games: int            # Count of games with this move count
    avg_bytes: float               # Average size of encoded game data
    results: str                   # Aggregated game results
    min_stored_count: Optional[int] # Minimum stored move count
    max_stored_count: Optional[int] # Maximum stored move count
    avg_stored_count: float        # Average stored move count

class PlayerPerformance(TypedDict):
    """Type definition for player performance statistics"""
    time_period: str              # Time period (month/year)
    games_played: int            # Total games played
    wins: int                    # Number of wins
    losses: int                  # Number of losses
    draws: int                   # Number of draws
    win_rate: float             # Win percentage
    avg_moves: float            # Average moves per game
    white_games: int            # Games played as white
    black_games: int            # Games played as black
    elo_rating: Optional[int]    # ELO rating if available

class OpeningStats(TypedDict):
    """Type definition for opening statistics"""
    eco_code: str               # ECO code of the opening
    opening_name: str           # Name of the opening
    games_played: int          # Number of games with this opening
    win_rate: float           # Win rate with this opening
    avg_moves: float          # Average game length with this opening

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
        # Cache for opening names to reduce database queries
        self.date_handler = DateHandler()
        self._opening_cache: Dict[str, str] = {}
        self._cache = {}
        self._cache_timeout = timedelta(minutes=5)

    async def _get_cached_data(self, key: str, fetch_fn):
        """Generic caching mechanism for repository methods."""
        cache_entry = self._cache.get(key)
        if cache_entry:
            timestamp, data = cache_entry
            if datetime.now() - timestamp < self._cache_timeout:
                self.logger.info("cache.hit", key=key)
                return data

        self.logger.info("cache.miss", key=key)
        data = await fetch_fn()
        self._cache[key] = (datetime.now(), data)
        return data
    
    async def get_player_performance_timeline(
        self,
        player_id: int,
        time_range: str = "monthly",  # 'monthly' or 'yearly'
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[PlayerPerformance]:
        """
        Analyze a player's performance over time.
        
        Args:
            player_id: Database ID of the player
            time_range: Aggregation period ('monthly' or 'yearly')
            start_date: Optional start date for analysis (YYYY-MM-DD)
            end_date: Optional end date for analysis (YYYY-MM-DD)
            
        Returns:
            List[PlayerPerformance]: Performance statistics over time
            
        Raises:
            ValueError: If player_id is invalid or dates are malformed
            SQLAlchemyError: On database operation failures
        """
        try:
            # Validate time range
            if time_range not in ('monthly', 'yearly'):
                raise ValueError("time_range must be 'monthly' or 'yearly'")

            # Construct date grouping expression based on time_range
            date_group = (
                "DATE_TRUNC('month', date)" if time_range == 'monthly'
                else "DATE_TRUNC('year', date)"
            )

            query = text(f"""
                WITH player_games AS (
                    SELECT
                        {date_group} as period,
                        date,
                        CASE
                            WHEN white_player_id = {player_id} THEN 'white'
                            ELSE 'black'
                        END as player_color,
                        CASE
                            WHEN white_player_id = {player_id} THEN white_elo
                            ELSE black_elo
                        END as player_elo,
                        result,
                        (octet_length(moves) - 19) / 2 as move_count,
                        CASE
                            WHEN (white_player_id = {player_id} AND result = '1-0') OR
                                 (black_player_id = {player_id} AND result = '0-1')
                                THEN 1
                            ELSE 0
                        END as is_win,
                        CASE
                            WHEN (white_player_id = {player_id} AND result = '0-1') OR
                                 (black_player_id = {player_id} AND result = '1-0')
                                THEN 1
                            ELSE 0
                        END as is_loss,
                        CASE
                            WHEN result = '1/2-1/2' THEN 1
                            ELSE 0
                        END as is_draw
                    FROM games
                    WHERE (white_player_id = {player_id} OR black_player_id = {player_id})
                )
                SELECT
                    period::date as time_period,
                    COUNT(*) as games_played,
                    SUM(is_win) as wins,
                    SUM(is_loss) as losses,
                    SUM(is_draw) as draws,
                    ROUND(AVG(move_count)::numeric, 2) as avg_moves,
                    SUM(CASE WHEN player_color = 'white' THEN 1 ELSE 0 END) as white_games,
                    SUM(CASE WHEN player_color = 'black' THEN 1 ELSE 0 END) as black_games,
                    ROUND(AVG(player_elo)::numeric, 0) as elo_rating,
                    ROUND((SUM(is_win)::float / COUNT(*) * 100)::numeric, 2) as win_rate
                FROM player_games
                WHERE date IS NOT NULL
                GROUP BY period
                ORDER BY period ASC;
            """)

            result = await self.db.execute(
                query,
                {
                    "player_id": player_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            rows = result.fetchall()
            
            # Process and validate results
            performance_data: List[PlayerPerformance] = []
            
            for row in rows:
                try:
                    stats = PlayerPerformance(
                        time_period=row[0].strftime(
                            '%Y-%m' if time_range == 'monthly' else '%Y'
                        ),
                        games_played=int(row[1]),
                        wins=int(row[2]),
                        losses=int(row[3]),
                        draws=int(row[4]),
                        avg_moves=float(row[5]),
                        white_games=int(row[6]),
                        black_games=int(row[7]),
                        elo_rating=int(row[8]) if row[8] is not None else None,
                        win_rate=float(row[9])
                    )
                    
                    # Validate statistics
                    if (stats['wins'] + stats['losses'] + stats['draws'] 
                            != stats['games_played']):
                        self.logger.warning(
                            f"Data inconsistency for period {stats['time_period']}"
                        )
                        continue
                        
                    if stats['white_games'] + stats['black_games'] != stats['games_played']:
                        self.logger.warning(
                            f"Color distribution mismatch for period {stats['time_period']}"
                        )
                        continue
                        
                    performance_data.append(stats)
                    
                except (TypeError, ValueError) as e:
                    self.logger.warning(
                        f"Error processing performance data: {e}",
                        exc_info=True
                    )
                    continue

            return performance_data

        except SQLAlchemyError as e:
            error_time = datetime.utcnow().isoformat()
            self.logger.error(
                "Player performance analysis failed",
                extra={
                    "timestamp": error_time,
                    "player_id": player_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"Error analyzing player performance: {str(e)}")

    async def get_player_opening_stats(
        self,
        player_id: int,
        min_games: int = 5
    ) -> List[OpeningStats]:
        """
        Analyze a player's performance with different openings.
        
        Args:
            player_id: Database ID of the player
            min_games: Minimum number of games with an opening to include in analysis
            
        Returns:
            List[OpeningStats]: Statistics for each opening played by the player
            
        Raises:
            ValueError: If player_id is invalid or min_games is negative
            SQLAlchemyError: On database operation failures
        """
        if min_games < 1:
            raise ValueError("min_games must be positive")

        try:
            query = text("""
                WITH player_openings AS (
                    SELECT
                        eco,
                        COUNT(*) as games_count,
                        ROUND(AVG((octet_length(moves) - 19) / 2)::numeric, 2) as avg_moves,
                        SUM(CASE
                            WHEN (white_player_id = :player_id AND result = '1-0') OR
                                 (black_player_id = :player_id AND result = '0-1')
                                THEN 1
                            ELSE 0
                        END)::float / COUNT(*) * 100 as win_rate
                    FROM games
                    WHERE (white_player_id = :player_id OR black_player_id = :player_id)
                        AND eco IS NOT NULL
                    GROUP BY eco
                    HAVING COUNT(*) >= :min_games
                )
                SELECT
                    po.eco as eco_code,
                    po.games_count as games_played,
                    po.win_rate,
                    po.avg_moves
                FROM player_openings po
                ORDER BY po.games_count DESC, po.win_rate DESC;
            """)

            result = await self.db.execute(
                query,
                {
                    "player_id": player_id,
                    "min_games": min_games
                }
            )
            
            rows = result.fetchall()
            
            # Process and validate results
            opening_stats: List[OpeningStats] = []
            
            for row in rows:
                try:
                    stats = OpeningStats(
                        eco_code=str(row[0]),
                        opening_name=self._get_opening_name(row[0]),  # Implement this helper
                        games_played=int(row[1]),
                        win_rate=float(row[2]),
                        avg_moves=float(row[3])
                    )
                    
                    # Validate statistics
                    if not (0 <= stats['win_rate'] <= 100):
                        self.logger.warning(
                            f"Invalid win rate for ECO {stats['eco_code']}: {stats['win_rate']}"
                        )
                        continue
                        
                    if stats['games_played'] < min_games:
                        continue
                        
                    opening_stats.append(stats)
                    
                except (TypeError, ValueError) as e:
                    self.logger.warning(
                        f"Error processing opening stats: {e}",
                        exc_info=True
                    )
                    continue

            return opening_stats

        except SQLAlchemyError as e:
            error_time = datetime.utcnow().isoformat()
            self.logger.error(
                "Opening analysis failed",
                extra={
                    "timestamp": error_time,
                    "player_id": player_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"Error analyzing opening statistics: {str(e)}")
    
    async def search_players(self, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for players by name with their most recent ELO rating.
        
        Args:
            search_query: Optional string to search for in player names
            
        Returns:
            List of dicts containing player id, name and most recent ELO
            
        Raises:
            SQLAlchemyError: On database operation failures
        """
        try:
            if not search_query:
                return []
                
            query = text("""
                SELECT id, name, 
                       (SELECT elo 
                        FROM (
                            SELECT CASE 
                                WHEN white_player_id = p.id THEN white_elo
                                ELSE black_elo
                            END as elo
                            FROM games g
                            WHERE (white_player_id = p.id OR black_player_id = p.id)
                            AND (white_elo > 0 OR black_elo > 0)
                            ORDER BY date DESC
                            LIMIT 1
                        ) recent_elo
                        WHERE elo > 0
                       ) as elo
                FROM players p
                WHERE name ILIKE :query
                ORDER BY 
                    CASE WHEN name ILIKE :exact_query THEN 0
                         WHEN name ILIKE :start_query THEN 1
                         ELSE 2
                    END,
                    LENGTH(name),
                    name
                LIMIT 10
            """)
            
            result = await self.db.execute(
                query,
                {
                    "query": f"%{search_query}%",
                    "exact_query": search_query,
                    "start_query": f"{search_query}%"
                }
            )
            
            return [
                {"id": row[0], "name": row[1], "elo": row[2]}
                for row in result.fetchall()
            ]
            
        except SQLAlchemyError as e:
            self.logger.error(f"Player search error: {str(e)}")
            raise
        
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

    async def _get_opening_name(self, eco_code: str) -> str:
        """
        Asynchronously retrieve the opening name for an ECO code.
        Uses caching to minimize database queries.
        
        Args:
            eco_code (str): The ECO code to look up
            
        Returns:
            str: The opening name or the ECO code if not found
        """
        try:
            # Check cache first
            if eco_code in self._opening_cache:
                return self._opening_cache[eco_code]

            # Query database for opening name
            query = text("""
                SELECT name 
                FROM openings 
                WHERE eco_code = :eco 
                LIMIT 1
            """)
            
            result = await self.db.execute(query, {"eco": eco_code})
            row = result.first()
            
            opening_name = row[0] if row else eco_code
            self._opening_cache[eco_code] = opening_name
            
            return opening_name
            
        except Exception as e:
            self.logger.warning(
                f"Failed to retrieve opening name for ECO {eco_code}: {str(e)}"
            )
            return eco_code

    async def _process_opening_data(self, row) -> OpeningAnalysis:
        """
        Process a database row into an OpeningAnalysis object.
        Handles all necessary async operations and data validation.
        
        Args:
            row: Database result row containing opening statistics
            
        Returns:
            OpeningAnalysis: Processed opening analysis object
            
        Raises:
            ValueError: If required data is missing or invalid
        """
        try:
            # Get opening name asynchronously
            opening_name = await self._get_opening_name(row.eco)

            # Process moves to find favorite response
            favorite_response = None
            if row.recent_moves:
                try:
                    moves = self.move_encoder.decode_moves(row.recent_moves)
                    if moves and len(moves) >= 4:
                        favorite_response = " ".join(moves[:4])
                except Exception as e:
                    self.logger.warning(
                        f"Failed to decode moves for ECO {row.eco}: {str(e)}"
                    )

            # Validate numeric data
            win_rate = float(row.win_rate)
            if not (0 <= win_rate <= 100):
                self.logger.warning(
                    f"Invalid win rate for ECO {row.eco}: {win_rate}"
                )
                win_rate = 0.0

            return OpeningAnalysis(
                eco_code=row.eco,
                opening_name=opening_name,
                total_games=row.total_games,
                win_count=row.wins,
                draw_count=row.draws,
                loss_count=row.losses,
                win_rate=win_rate,
                avg_game_length=row.avg_moves,
                games_as_white=row.white_games,
                games_as_black=row.black_games,
                avg_opponent_rating=int(row.avg_opponent_elo) if row.avg_opponent_elo else None,
                last_played=row.last_played,
                favorite_response=favorite_response
            )
        except Exception as e:
            raise ValueError(f"Error processing opening data: {str(e)}")

    async def get_player_opening_analysis(
        self,
        player_id: int,
        min_games: int = 5,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> OpeningAnalysisResponse:
        """
        Analyze a player's performance with different chess openings.
        
        Args:
            player_id (int): Database ID of the player to analyze
            min_games (int): Minimum number of games threshold (default: 5)
            start_date (Optional[str]): Start date for analysis (YYYY-MM-DD)
            end_date (Optional[str]): End date for analysis (YYYY-MM-DD)
        
        Returns:
            OpeningAnalysisResponse: Detailed opening statistics and analysis
        
        Raises:
            ValueError: If input parameters are invalid or no data found
            SQLAlchemyError: On database operation failures
        """
        
        try:
            # Input validation with detailed error messages
            if not isinstance(player_id, int) or player_id <= 0:
                raise ValueError(
                    f"player_id must be a positive integer, got: {type(player_id)}, value: {player_id}"
                )
            if not isinstance(min_games, int) or min_games < 1:
                raise ValueError(
                    f"min_games must be a positive integer, got: {type(min_games)}, value: {min_games}"
                )

            # Initialize parameter dictionary with required parameters
            params = {
                "player_id": player_id,
                "min_games": min_games
            }

            # Validate and add date parameters if provided
            date_conditions = []
            if start_date:
                try:
                    datetime.strptime(start_date, '%Y-%m-%d')
                    date_conditions.append("date >= :start_date::date")
                    params["start_date"] = start_date
                except ValueError as e:
                    raise ValueError(f"Invalid start_date format: {str(e)}")

            if end_date:
                try:
                    datetime.strptime(end_date, '%Y-%m-%d')
                    date_conditions.append("date <= :end_date::date")
                    params["end_date"] = end_date
                except ValueError as e:
                    raise ValueError(f"Invalid end_date format: {str(e)}")

            # Construct date filter clause
            date_filter = " AND " + " AND ".join(date_conditions) if date_conditions else ""

            # Define the query with explicit parameter references
            query = text(f"""
                WITH game_stats AS (
                    -- Base statistics per opening
                    SELECT
                        eco,
                        COUNT(*) as total_games,
                        SUM(CASE
                            WHEN (white_player_id = :player_id AND result = '1-0') OR
                                (black_player_id = :player_id AND result = '0-1')
                            THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as draws,
                        SUM(CASE
                            WHEN (white_player_id = :player_id AND result = '0-1') OR
                                (black_player_id = :player_id AND result = '1-0')
                            THEN 1 ELSE 0 END) as losses,
                        ROUND(AVG((octet_length(moves) - 19) / 2)::numeric, 2) as avg_moves,
                        SUM(CASE WHEN white_player_id = :player_id THEN 1 ELSE 0 END) as white_games,
                        SUM(CASE WHEN black_player_id = :player_id THEN 1 ELSE 0 END) as black_games,
                        ROUND(AVG(
                            CASE
                                WHEN white_player_id = :player_id THEN black_elo
                                ELSE white_elo
                            END
                        )::numeric, 0) as avg_opponent_elo,
                        MAX(date) as last_played
                    FROM games
                    WHERE (white_player_id = :player_id OR black_player_id = :player_id)
                        AND eco IS NOT NULL
                        {date_filter}
                    GROUP BY eco
                    HAVING COUNT(*) >= :min_games
                ),
                moves_data AS (
                    -- Latest moves per opening
                    SELECT DISTINCT ON (eco)
                        eco,
                        moves
                    FROM games
                    WHERE (white_player_id = :player_id OR black_player_id = :player_id)
                        AND eco IS NOT NULL
                        {date_filter}
                    ORDER BY eco, date DESC
                ),
                aggregated_stats AS (
                    -- Calculate win rates and rankings with null handling
                    SELECT 
                        gs.*,
                        ROUND((gs.wins::float / NULLIF(gs.total_games, 0) * 100)::numeric, 2) as win_rate,
                        RANK() OVER (
                            ORDER BY gs.wins::float / NULLIF(gs.total_games, 0) DESC NULLS LAST
                        ) as win_rank,
                        RANK() OVER (
                            ORDER BY gs.total_games DESC
                        ) as popularity_rank
                    FROM game_stats gs
                ),
                summary AS (
                    -- Overall summary statistics
                    SELECT
                        COUNT(*) as total_openings,
                        ROUND(AVG(avg_moves)::numeric, 2) as overall_avg_moves,
                        (SELECT eco FROM aggregated_stats WHERE win_rank = 1 LIMIT 1) as best_eco,
                        (SELECT eco FROM aggregated_stats WHERE popularity_rank = 1 LIMIT 1) as most_played
                    FROM aggregated_stats
                )
                -- Final result combining all statistics
                SELECT
                    ast.*,
                    md.moves as recent_moves,
                    s.total_openings,
                    s.overall_avg_moves,
                    s.best_eco,
                    s.most_played
                FROM aggregated_stats ast
                JOIN moves_data md ON ast.eco = md.eco
                CROSS JOIN summary s
                ORDER BY ast.total_games DESC, ast.win_rate DESC NULLS LAST;
            """)

            # Execute query with validated parameters
            self.logger.debug(f"Executing query with parameters: {params}")
            result = await self.db.execute(query, params)
            rows = result.fetchall()

            if not rows:
                raise ValueError(
                    f"No opening statistics found for player {player_id} "
                    f"within the specified date range"
                )

            # Process results into response objects
            analyses = []
            summary_stats = None

            for row in rows:
                try:
                    # Process game moves for favorite response
                    favorite_response = None
                    if row.recent_moves:
                        try:
                            moves = self.move_encoder.decode_moves(row.recent_moves)
                            if moves and len(moves) >= 4:
                                favorite_response = " ".join(moves[:4])
                        except Exception as e:
                            self.logger.warning(
                                f"Error decoding moves for ECO {row.eco}: {str(e)}"
                            )

                    # Create opening analysis object with validation
                    analysis = OpeningAnalysis(
                        eco_code=row.eco,
                        opening_name=await self._get_opening_name(row.eco),
                        total_games=row.total_games,
                        win_count=row.wins,
                        draw_count=row.draws,
                        loss_count=row.losses,
                        win_rate=row.win_rate if row.win_rate is not None else 0.0,
                        avg_game_length=row.avg_moves,
                        games_as_white=row.white_games,
                        games_as_black=row.black_games,
                        avg_opponent_rating=int(row.avg_opponent_elo) if row.avg_opponent_elo else None,
                        last_played=row.last_played,
                        favorite_response=favorite_response
                    )
                    analyses.append(analysis)

                    # Store summary statistics from first row
                    if summary_stats is None:
                        summary_stats = {
                            'total_openings': row.total_openings,
                            'most_successful': row.best_eco,
                            'most_played': row.most_played,
                            'avg_game_length': row.overall_avg_moves
                        }

                except Exception as e:
                    self.logger.error(
                        f"Error processing opening data for ECO {row.eco}: {str(e)}",
                        exc_info=True
                    )
                    continue

            if not analyses:
                raise ValueError("Failed to process any opening statistics")

            return OpeningAnalysisResponse(
                analysis=analyses,
                **summary_stats
            )

        except SQLAlchemyError as e:
            error_time = datetime.utcnow().isoformat()
            self.logger.error(
                "Database error in opening analysis",
                extra={
                    "timestamp": error_time,
                    "player_id": player_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"Database error in opening analysis: {str(e)}")
        
    async def get_database_metrics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        Retrieve comprehensive database metrics including performance stats and growth trends.
        
        Args:
            start_date: Optional start date for trend analysis (YYYY-MM-DD)
            end_date: Optional end date for trend analysis (YYYY-MM-DD)
            
        Returns:
            DatabaseMetricsResponse containing current stats and historical trends
            
        Raises:
            ValueError: If date parameters are invalid
            SQLAlchemyError: On database operation failures
        """
        try:
            # Get current database statistics
            basic_stats = await self._get_basic_stats()
            performance_metrics = await self._get_performance_metrics()
            growth_trends = await self._get_growth_trends(start_date, end_date)
            health_metrics = await self._get_health_metrics()
            
            return {
                # Current statistics
                "total_games": basic_stats["total_games"],
                "total_players": basic_stats["total_players"],
                "total_openings": basic_stats["total_openings"],
                "storage_size": basic_stats["storage_size"],
                
                # Performance metrics
                "avg_query_time": performance_metrics["avg_query_time"],
                "queries_per_second": performance_metrics["queries_per_second"],
                "cache_hit_ratio": performance_metrics["cache_hit_ratio"],
                
                # Growth and performance trends
                "growth_trend": growth_trends,
                "query_performance": performance_metrics["query_stats"],
                
                # Health and capacity
                "index_health": health_metrics["index_health"],
                "replication_lag": health_metrics["replication_lag"],
                "capacity_used": health_metrics["capacity_used"],
                "estimated_capacity_date": health_metrics["estimated_capacity_date"]
            }
            
        except ValueError as e:
            self.logger.error(f"Invalid parameters in database metrics query: {str(e)}")
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error in metrics collection: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in metrics collection: {str(e)}")
            raise

    async def _get_basic_stats(self) -> Dict:
        """Get current database statistics"""
        query = text("""
            SELECT
                (SELECT COUNT(*) FROM games) as total_games,
                (SELECT COUNT(*) FROM players) as total_players,
                (SELECT COUNT(DISTINCT eco) FROM games) as total_openings,
                pg_database_size(current_database()) / (1024 * 1024.0) as storage_size
            FROM (SELECT 1) as t
        """)
        
        result = await self.db.execute(query)
        row = result.fetchone()
        
        return {
            "total_games": row[0],
            "total_players": row[1],
            "total_openings": row[2],
            "storage_size": float(row[3])
        }

    async def _get_performance_metrics(self) -> Dict:
        """Get database performance statistics"""
        query = text("""
            WITH query_stats AS (
                SELECT * FROM pg_stat_statements
                WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
            )
            SELECT
                AVG(mean_exec_time) as avg_query_time,
                SUM(calls) / EXTRACT(EPOCH FROM (NOW() - stats_reset)) as qps,
                (SUM(shared_blks_hit) * 100.0) / 
                NULLIF(SUM(shared_blks_hit + shared_blks_read), 0) as cache_hit_ratio,
                queryid,
                query,
                mean_exec_time,
                calls / EXTRACT(EPOCH FROM (NOW() - stats_reset)) * 60 as calls_per_minute,
                (total_exec_time / NULLIF(calls, 0)) as avg_exec_time
            FROM query_stats
            GROUP BY queryid, query, mean_exec_time, calls, total_exec_time, stats_reset
            ORDER BY mean_exec_time DESC
            LIMIT 10
        """)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        if not rows:
            return {
                "avg_query_time": 0,
                "queries_per_second": 0,
                "cache_hit_ratio": 0,
                "query_stats": []
            }
            
        return {
            "avg_query_time": float(rows[0][0]),
            "queries_per_second": float(rows[0][1]),
            "cache_hit_ratio": float(rows[0][2]),
            "query_stats": [
                {
                    "query_type": self._categorize_query(row[4]),
                    "avg_execution_time": float(row[5]),
                    "calls_per_minute": float(row[6]),
                    "error_rate": 0.0  # Would need additional monitoring for real error rates
                }
                for row in rows
            ]
        }

    async def _get_growth_trends(
        self,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> List[Dict]:
        """Get database growth trends over time"""
        query = text("""
            WITH RECURSIVE dates AS (
                SELECT :start_date::date as date
                UNION ALL
                SELECT date + interval '1 day'
                FROM dates
                WHERE date < :end_date::date
            ),
            daily_stats AS (
                SELECT
                    date_trunc('day', games.date) as stat_date,
                    COUNT(*) as game_count,
                    COUNT(DISTINCT CASE WHEN games.white_player_id IS NOT NULL 
                        THEN games.white_player_id END +
                        CASE WHEN games.black_player_id IS NOT NULL 
                        THEN games.black_player_id END) as player_count,
                    SUM(octet_length(moves)) / (1024 * 1024.0) as storage_mb
                FROM games
                WHERE games.date BETWEEN :start_date AND :end_date
                GROUP BY date_trunc('day', games.date)
            )
            SELECT
                d.date,
                COALESCE(ds.game_count, 0) as games,
                COALESCE(ds.player_count, 0) as players,
                COALESCE(ds.storage_mb, 0) as storage
            FROM dates d
            LEFT JOIN daily_stats ds ON d.date = ds.stat_date
            ORDER BY d.date
        """)
        
        result = await self.db.execute(
            query,
            {
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        rows = result.fetchall()
        
        return [
            {
                "date": row[0],
                "total_games": row[1],
                "total_players": row[2],
                "storage_used": float(row[3])
            }
            for row in rows
        ]

    async def _get_health_metrics(self) -> Dict:
        """Get database health and capacity metrics"""
        query = text("""
            WITH index_stats AS (
                SELECT
                    schemaname,
                    tablename,
                    indexrelname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE idx_scan > 0
            ),
            table_stats AS (
                SELECT
                    pg_table_size(c.oid) as table_size
                FROM pg_class c
                LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                AND c.relkind = 'r'
            )
            SELECT
                (SELECT COALESCE(AVG(idx_tup_fetch::float / NULLIF(idx_tup_read, 0)), 0) * 100
                FROM index_stats) as index_efficiency,
                (SELECT COALESCE(SUM(table_size), 0) FROM table_stats) as total_size,
                (SELECT setting::float FROM pg_settings WHERE name = 'max_connections') as max_connections,
                (SELECT COUNT(*) FROM pg_stat_activity) as current_connections
        """)
        
        result = await self.db.execute(query)
        row = result.fetchone()
        
        # Calculate capacity metrics
        total_size = float(row[1])
        max_size = 1024 * 1024 * 1024 * 100  # 100GB example limit
        capacity_used = (total_size / max_size) * 100
        
        # Project capacity date based on growth rate
        growth_rate = 1024 * 1024 * 10  # 10MB per day example
        days_until_full = (max_size - total_size) / growth_rate
        capacity_date = datetime.now() + timedelta(days=days_until_full)
        
        return {
            "index_health": float(row[0]),
            "replication_lag": 0.0,  # Would need replication setup for real lag
            "capacity_used": capacity_used,
            "estimated_capacity_date": capacity_date if capacity_used < 95 else None
        }

    def _categorize_query(self, query_text: str) -> str:
        """Categorize SQL query by type"""
        query_text = query_text.lower()
        if "select" in query_text:
            if "games" in query_text:
                return "game_search"
            elif "players" in query_text:
                return "player_search"
            elif "count" in query_text:
                return "analytics"
        return "other"