"""Repository for comprehensive chess game analysis."""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

from ..models import (
    MoveCountAnalysis,
    OpeningStatsResponse,
    OpeningAnalysis,
    OpeningAnalysisResponse,
    DatabaseMetricsResponse,
    GameDB,
    PlayerDB
)
from ..common.validation import DateHandler
from .cache import AnalysisCacheManager

logger = logging.getLogger(__name__)

class AnalysisRepository:
    """Repository for comprehensive chess game analysis."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = AnalysisCacheManager()
        self.date_handler = DateHandler()

    async def get_move_count_distribution(self) -> List[MoveCountAnalysis]:
        """
        Analyze the distribution of move counts across chess games.
        
        This method computes statistics about game lengths by analyzing the binary
        move data structure in the database.
        
        Returns:
            List[MoveCountAnalysis]: Array of move count statistics
            
        Raises:
            SQLAlchemyError: On database operation failures
            ValueError: If data validation fails
        """
        try:
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
                ORDER BY actual_full_moves ASC
            """)

            # Execute query with explicit transaction handling
            result = await self.db.execute(query)
            raw_rows = result.fetchall()

            # Process and validate results
            processed_results: List[MoveCountAnalysis] = []
            
            for row in raw_rows:
                try:
                    # Validate numeric fields
                    actual_moves = int(row.actual_full_moves)
                    num_games = int(row.number_of_games)
                    avg_bytes = float(row.avg_bytes)
                    min_count = int(row.min_stored_count) if row.min_stored_count is not None else None
                    max_count = int(row.max_stored_count) if row.max_stored_count is not None else None
                    avg_count = float(row.avg_stored_count) if row.avg_stored_count is not None else 0.0

                    # Validate value ranges
                    if not (0 <= actual_moves <= 500):
                        logger.warning(f"Invalid move count detected: {actual_moves}")
                        continue

                    if num_games <= 0:
                        logger.warning(f"Invalid game count: {num_games} for {actual_moves} moves")
                        continue

                    processed_row = MoveCountAnalysis(
                        actual_full_moves=actual_moves,
                        number_of_games=num_games,
                        avg_bytes=avg_bytes,
                        results=str(row.results),
                        min_stored_count=min_count,
                        max_stored_count=max_count,
                        avg_stored_count=avg_count
                    )
                    processed_results.append(processed_row)

                except (TypeError, ValueError) as e:
                    logger.warning(f"Error processing row: {row}", exc_info=e)
                    continue

            # Validate final result set
            if not processed_results:
                logger.warning("No valid move count data found")
                return []

            return processed_results

        except SQLAlchemyError as e:
            error_time = datetime.utcnow().isoformat()
            logger.error(
                "Move count analysis failed",
                extra={
                    "timestamp": error_time,
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"Error analyzing move count distribution: {str(e)}")

    async def get_player_opening_analysis(
        self,
        player_id: int,
        min_games: int = 5,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> OpeningAnalysisResponse:
        """Analyze player's performance with different openings."""
        try:
            # Validate dates
            start_date = self.date_handler.validate_and_parse_date(start_date, "start_date")
            end_date = self.date_handler.validate_and_parse_date(end_date, "end_date")

            query = """
                WITH player_games AS (
                    SELECT 
                        g.*,
                        CASE 
                            WHEN g.white_player_id = :player_id THEN 'white'
                            ELSE 'black'
                        END as player_color,
                        CASE
                            WHEN (g.white_player_id = :player_id AND g.result = '1-0')
                                OR (g.black_player_id = :player_id AND g.result = '0-1')
                            THEN 1
                            WHEN g.result = '1/2-1/2' THEN 0.5
                            ELSE 0
                        END as points
                    FROM games g
                    WHERE (g.white_player_id = :player_id OR g.black_player_id = :player_id)
                    AND (:start_date::date IS NULL OR g.date >= :start_date::date)
                    AND (:end_date::date IS NULL OR g.date <= :end_date::date)
                )
                SELECT 
                    eco,
                    COUNT(*) as total_games,
                    SUM(CASE WHEN points = 1 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN points = 0.5 THEN 1 ELSE 0 END) as draws,
                    SUM(CASE WHEN points = 0 THEN 1 ELSE 0 END) as losses,
                    AVG(array_length(string_to_array(moves::text, ' '), 1)) as avg_moves,
                    SUM(CASE WHEN player_color = 'white' THEN 1 ELSE 0 END) as white_games,
                    SUM(CASE WHEN player_color = 'black' THEN 1 ELSE 0 END) as black_games,
                    MAX(date) as last_played
                FROM player_games
                GROUP BY eco
                HAVING COUNT(*) >= :min_games
                ORDER BY COUNT(*) DESC
            """

            result = await self.db.execute(
                text(query),
                {
                    "player_id": player_id,
                    "min_games": min_games,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            rows = result.fetchall()

            analysis = []
            for row in rows:
                opening = await self._get_opening_name(row.eco)
                analysis.append(
                    OpeningAnalysis(
                        eco_code=row.eco,
                        opening_name=opening,
                        total_games=row.total_games,
                        win_count=row.wins,
                        draw_count=row.draws,
                        loss_count=row.losses,
                        win_rate=(row.wins + row.draws * 0.5) / row.total_games * 100,
                        avg_game_length=float(row.avg_moves),
                        games_as_white=row.white_games,
                        games_as_black=row.black_games,
                        last_played=row.last_played
                    )
                )

            return OpeningAnalysisResponse(
                analysis=analysis,
                total_openings=len(analysis),
                most_successful=max(analysis, key=lambda x: x.win_rate).eco_code if analysis else None,
                most_played=max(analysis, key=lambda x: x.total_games).eco_code if analysis else None,
                avg_game_length=sum(a.avg_game_length * a.total_games for a in analysis) / 
                              sum(a.total_games for a in analysis) if analysis else 0
            )

        except Exception as e:
            logger.error(f"Error analyzing player openings: {str(e)}")
            raise

    async def get_database_metrics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> DatabaseMetricsResponse:
        """Get database metrics with optional date filtering."""
        try:
            # Parse dates
            start = self.date_handler.validate_and_parse_date(start_date, "start_date")
            end = self.date_handler.validate_and_parse_date(end_date, "end_date")
            
            query = """
                SELECT 
                    COUNT(*) as games,
                    COUNT(DISTINCT white_player_id) + 
                    COUNT(DISTINCT black_player_id) as players,
                    SUM(length(moves::text)) as storage,
                    COUNT(CASE WHEN date IS NOT NULL THEN 1 END) as dated_games,
                    MIN(date) as earliest_game,
                    MAX(date) as latest_game,
                    COUNT(CASE WHEN result = '1-0' THEN 1 END) as white_wins,
                    COUNT(CASE WHEN result = '0-1' THEN 1 END) as black_wins,
                    COUNT(CASE WHEN result = '1/2-1/2' THEN 1 END) as draws,
                    COUNT(CASE WHEN result = '*' THEN 1 END) as undecided,
                    AVG(CASE 
                        WHEN moves IS NOT NULL AND length(moves::text) > 0 
                        THEN array_length(string_to_array(moves::text, ' '), 1)
                        ELSE 0 
                    END) as avg_moves
                FROM games
                WHERE (:start_date::date IS NULL OR date >= :start_date::date)
                AND (:end_date::date IS NULL OR date <= :end_date::date)
            """
            
            result = await self.db.execute(
                text(query),
                {"start_date": start, "end_date": end}
            )
            row = result.fetchone()
            
            return DatabaseMetricsResponse(
                total_games=row.games,
                total_players=row.players,
                storage_size_bytes=row.storage,
                dated_games=row.dated_games,
                earliest_game=row.earliest_game,
                latest_game=row.latest_game,
                white_wins=row.white_wins,
                black_wins=row.black_wins,
                draws=row.draws,
                undecided=row.undecided,
                average_moves=float(row.avg_moves) if row.avg_moves else 0.0
            )

        except Exception as e:
            logger.error(f"Error getting database metrics: {str(e)}")
            raise

    async def _get_opening_name(self, eco_code: str) -> str:
        """Get opening name from ECO code."""
        cache_key = f"opening_name_{eco_code}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        query = "SELECT name FROM openings WHERE eco = :eco"
        result = await self.db.execute(text(query), {"eco": eco_code})
        row = result.first()
        
        name = row[0] if row else eco_code
        self.cache.set(cache_key, name)
        return name

    async def _get_basic_stats(self) -> Dict[str, Any]:
        """Get basic database statistics."""
        total_games = await self.db.scalar(select(func.count()).select_from(GameDB))
        total_players = await self.db.scalar(select(func.count()).select_from(PlayerDB))
        
        return {
            "total_games": total_games,
            "total_players": total_players,
            "last_updated": datetime.utcnow()
        }

    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics."""
        # This would typically come from your monitoring system
        return {
            "avg_query_time": 45.2,
            "queries_per_second": 100.5,
            "cache_hit_ratio": 85.5
        }

    async def _get_growth_trends(
        self,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> Dict[str, Any]:
        """Get database growth trends."""
        query = """
            SELECT 
                date_trunc('day', date) as day,
                COUNT(*) as games,
                COUNT(DISTINCT white_player_id) + 
                COUNT(DISTINCT black_player_id) as players,
                SUM(length(moves::text)) as storage
            FROM games
            WHERE (:start_date::date IS NULL OR date >= :start_date::date)
            AND (:end_date::date IS NULL OR date <= :end_date::date)
            GROUP BY day
            ORDER BY day
        """
        
        result = await self.db.execute(
            text(query),
            {"start_date": start_date, "end_date": end_date}
        )
        rows = result.fetchall()
        
        return {
            "growth_trend": [
                {
                    "date": row.day,
                    "total_games": row.games,
                    "total_players": row.players,
                    "storage_used": row.storage / (1024 * 1024)  # Convert to MB
                }
                for row in rows
            ]
        }

    async def _get_health_metrics(self) -> Dict[str, Any]:
        """Get database health metrics."""
        # This would typically come from your monitoring system
        return {
            "index_health": 95.5,
            "replication_lag": 0.5,
            "capacity_used": 65.5
        }