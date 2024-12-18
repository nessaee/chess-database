"""Repository for comprehensive chess game analysis."""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

from ..models import (
    MoveCountAnalysis,
    OpeningAnalysis,
    OpeningAnalysisResponse,
    DatabaseMetricsResponse,
    EndpointMetrics,
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
        Get the distribution of move counts across chess games from the materialized view.
        
        Returns:
            List[MoveCountAnalysis]: Array of move count statistics
            
        Raises:
            SQLAlchemyError: On database operation failures
            ValueError: If data validation fails
        """
        try:
            query = text("""
                SELECT 
                    actual_full_moves,
                    number_of_games,
                    avg_bytes,
                    last_updated
                FROM move_count_stats
                ORDER BY actual_full_moves ASC
            """)

            # Execute query
            result = await self.db.execute(query)
            raw_rows = result.fetchall()

            # Process and validate results
            processed_results: List[MoveCountAnalysis] = []
            
            for row in raw_rows:
                try:
                    processed_results.append(
                        MoveCountAnalysis(
                            move_count=row.actual_full_moves,
                            game_count=row.number_of_games,
                            avg_bytes=float(row.avg_bytes)
                        )
                    )
                except (ValueError, AttributeError) as e:
                    logger.error(f"Error processing move count row: {e}")
                    continue

            return processed_results

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_move_count_distribution: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_move_count_distribution: {e}")
            raise ValueError(f"Error processing move count data: {str(e)}")

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

            # Base query using the materialized view
            query = """
                SELECT 
                    pos.opening_id,
                    o.name as opening_name,
                    o.eco_code,
                    pos.total_games,
                    pos.wins,
                    pos.draws,
                    pos.losses,
                    pos.avg_moves,
                    pos.white_games,
                    pos.black_games,
                    pos.last_played,
                    pos.win_rate
                FROM player_opening_stats pos
                JOIN openings o ON o.id = pos.opening_id
                WHERE pos.player_id = :player_id
                AND pos.total_games >= :min_games
                AND (:start_date::date IS NULL OR pos.last_played >= :start_date::date)
                AND (:end_date::date IS NULL OR pos.last_played <= :end_date::date)
                ORDER BY pos.total_games DESC
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
                analysis.append(
                    OpeningAnalysis(
                        eco_code=row.eco_code,
                        opening_name=row.opening_name,
                        total_games=row.total_games,
                        win_count=row.wins,
                        draw_count=row.draws,
                        loss_count=row.losses,
                        win_rate=row.win_rate,
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

    async def get_database_metrics(self) -> DatabaseMetricsResponse:
        """Get database metrics."""
        try:
            # Combine basic stats, performance metrics, and health metrics into a single query
            combined_query = """
                WITH game_stats AS (
                    SELECT
                        COUNT(*) as total_games,
                        COUNT(DISTINCT COALESCE(white_player_id, black_player_id)) as total_players,
                        AVG(array_length(string_to_array(moves::text, ' '), 1)) as avg_moves_per_game,
                        AVG(CASE WHEN result = '1-0' THEN 1 WHEN result = '0-1' THEN 0 ELSE 0.5 END) as white_win_rate,
                        COUNT(CASE WHEN result = '1/2-1/2' THEN 1 END)::float / NULLIF(COUNT(*), 0) as draw_rate,
                        COUNT(CASE WHEN moves IS NULL THEN 1 END)::float / NULLIF(COUNT(*), 0) as null_moves_rate,
                        COUNT(CASE WHEN white_player_id IS NULL OR black_player_id IS NULL THEN 1 END)::float / NULLIF(COUNT(*), 0) as missing_player_rate,
                        COUNT(CASE WHEN result IS NULL THEN 1 END)::float / NULLIF(COUNT(*), 0) as missing_result_rate
                    FROM games
                ),
                monthly_stats AS (
                    SELECT
                        DATE_TRUNC('month', date) as month,
                        COUNT(*) as games_added,
                        COUNT(DISTINCT COALESCE(white_player_id, black_player_id)) as active_players
                    FROM games
                    WHERE date IS NOT NULL
                    GROUP BY DATE_TRUNC('month', date)
                    ORDER BY month DESC
                    LIMIT 12
                ),
                growth_stats AS (
                    SELECT
                        COALESCE(AVG(games_added), 0) as avg_monthly_games,
                        COALESCE(AVG(active_players), 0) as avg_monthly_players,
                        COALESCE(MAX(games_added), 0) as peak_monthly_games,
                        COALESCE(MAX(active_players), 0) as peak_monthly_players
                    FROM monthly_stats
                )
                SELECT
                    g.*,
                    gr.avg_monthly_games,
                    gr.avg_monthly_players,
                    gr.peak_monthly_games,
                    gr.peak_monthly_players
                FROM game_stats g
                CROSS JOIN growth_stats gr
            """
            
            result = await self.db.execute(text(combined_query))
            row = result.fetchone()
            
            # Get endpoint metrics from materialized view without refreshing
            endpoint_metrics = await self._get_endpoint_metrics()
            
            return DatabaseMetricsResponse(
                total_games=row.total_games,
                total_players=row.total_players,
                avg_moves_per_game=float(row.avg_moves_per_game or 0),
                avg_game_duration=0.0,  # Not implemented
                performance={
                    "white_win_rate": float(row.white_win_rate or 0),
                    "draw_rate": float(row.draw_rate or 0),
                    "avg_game_length": float(row.avg_moves_per_game or 0)
                },
                growth_trends={
                    "avg_monthly_games": float(row.avg_monthly_games),
                    "avg_monthly_players": float(row.avg_monthly_players),
                    "peak_monthly_games": int(row.peak_monthly_games),
                    "peak_monthly_players": int(row.peak_monthly_players)
                },
                health_metrics={
                    "null_moves_rate": float(row.null_moves_rate),
                    "missing_player_rate": float(row.missing_player_rate),
                    "missing_result_rate": float(row.missing_result_rate)
                },
                endpoint_metrics=endpoint_metrics
            )
            
        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            raise

    async def _get_endpoint_metrics(self) -> List[EndpointMetrics]:
        """Get endpoint performance metrics from the materialized view."""
        try:
            # Try to refresh the materialized view if needed
            try:
                refresh_result = await self.db.execute(text("SELECT refresh_endpoint_performance_stats()"))
                refresh_success = refresh_result.scalar()
                await self.db.commit()
                if refresh_success:
                    logger.info("Successfully refreshed endpoint metrics view")
            except Exception as e:
                logger.warning(f"Failed to refresh endpoint metrics view: {e}")
                # Continue with potentially stale data
            
            # Query the materialized view
            query = """
                WITH last_refresh AS (
                    SELECT last_refresh, refresh_in_progress
                    FROM materialized_view_refresh_status
                    WHERE view_name = 'endpoint_performance_stats'
                )
                SELECT 
                    m.*,
                    r.last_refresh,
                    r.refresh_in_progress
                FROM endpoint_performance_stats m
                CROSS JOIN last_refresh r
                ORDER BY m.total_calls DESC
            """
            
            result = await self.db.execute(text(query))
            rows = result.fetchall()
            
            metrics = []
            for row in rows:
                metrics.append({
                    "endpoint": row.endpoint,
                    "method": row.method,
                    "total_calls": row.total_calls,
                    "successful_calls": row.successful_calls,
                    "error_count": row.error_count,
                    "avg_response_time": float(row.avg_response_time_ms) if row.avg_response_time_ms is not None else 0.0,
                    "p95_response_time": float(row.p95_response_time_ms) if row.p95_response_time_ms is not None else 0.0,
                    "p99_response_time": float(row.p99_response_time_ms) if row.p99_response_time_ms is not None else 0.0,
                    "max_response_time": float(row.max_response_time_ms) if row.max_response_time_ms is not None else 0.0,
                    "min_response_time": float(row.min_response_time_ms) if row.min_response_time_ms is not None else 0.0,
                    "success_rate": float(row.success_rate) if row.success_rate is not None else 0.0,
                    "error_rate": float(row.error_rate) if row.error_rate is not None else 0.0,
                    "avg_response_size": float(row.avg_response_size_bytes) if row.avg_response_size_bytes is not None else 0.0,
                    "max_response_size": row.max_response_size_bytes if row.max_response_size_bytes is not None else 0,
                    "min_response_size": row.min_response_size_bytes if row.min_response_size_bytes is not None else 0,
                    "error_messages": row.error_messages or [],
                    "last_refresh": row.last_refresh.isoformat() if row.last_refresh else None,
                    "refresh_in_progress": row.refresh_in_progress
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting endpoint metrics: {e}")
            return []

    async def _get_basic_stats(self) -> Dict[str, Any]:
        """Get basic database statistics."""
        query = """
            SELECT
                COUNT(*) as total_games,
                COUNT(DISTINCT COALESCE(white_player_id, black_player_id)) as total_players,
                AVG(array_length(string_to_array(moves::text, ' '), 1)) as avg_moves_per_game,
                0 as avg_game_duration
            FROM games
        """
        result = await self.db.execute(text(query))
        row = result.fetchone()
        return {
            "total_games": row.total_games if row else 0,
            "total_players": row.total_players if row else 0,
            "avg_moves_per_game": float(row.avg_moves_per_game) if row and row.avg_moves_per_game else 0.0,
            "avg_game_duration": 0.0
        }

    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics."""
        query = """
            SELECT
                AVG(CASE WHEN result = '1-0' THEN 1 WHEN result = '0-1' THEN 0 ELSE 0.5 END) as white_win_rate,
                COUNT(CASE WHEN result = '1/2-1/2' THEN 1 END)::float / NULLIF(COUNT(*), 0) as draw_rate,
                AVG(array_length(string_to_array(moves::text, ' '), 1)) as avg_game_length
            FROM games
            WHERE result IS NOT NULL
        """
        result = await self.db.execute(text(query))
        row = result.fetchone()
        return {
            "white_win_rate": float(row.white_win_rate) if row and row.white_win_rate else 0.0,
            "draw_rate": float(row.draw_rate) if row and row.draw_rate else 0.0,
            "avg_game_length": float(row.avg_game_length) if row and row.avg_game_length else 0.0
        }

    async def _get_growth_trends(self) -> Dict[str, Any]:
        """Get database growth trends."""
        query = """
            WITH monthly_stats AS (
                SELECT
                    DATE_TRUNC('month', date) as month,
                    COUNT(*) as games_added,
                    COUNT(DISTINCT COALESCE(white_player_id, black_player_id)) as active_players
                FROM games
                WHERE date IS NOT NULL
                GROUP BY DATE_TRUNC('month', date)
                ORDER BY month DESC
                LIMIT 12
            )
            SELECT
                COALESCE(AVG(games_added), 0) as avg_monthly_games,
                COALESCE(AVG(active_players), 0) as avg_monthly_players,
                COALESCE(MAX(games_added), 0) as peak_monthly_games,
                COALESCE(MAX(active_players), 0) as peak_monthly_players
            FROM monthly_stats
        """
        result = await self.db.execute(text(query))
        row = result.fetchone()
        return {
            "avg_monthly_games": float(row.avg_monthly_games) if row else 0.0,
            "avg_monthly_players": float(row.avg_monthly_players) if row else 0.0,
            "peak_monthly_games": int(row.peak_monthly_games) if row else 0,
            "peak_monthly_players": int(row.peak_monthly_players) if row else 0
        }

    async def _get_health_metrics(self) -> Dict[str, Any]:
        """Get database health metrics."""
        query = """
            SELECT
                COALESCE(COUNT(CASE WHEN moves IS NULL THEN 1 END)::float / NULLIF(COUNT(*), 0), 0) as null_moves_rate,
                COALESCE(COUNT(CASE WHEN white_player_id IS NULL OR black_player_id IS NULL THEN 1 END)::float / NULLIF(COUNT(*), 0), 0) as missing_player_rate,
                COALESCE(COUNT(CASE WHEN result IS NULL THEN 1 END)::float / NULLIF(COUNT(*), 0), 0) as missing_result_rate
            FROM games
        """
        result = await self.db.execute(text(query))
        row = result.fetchone()
        return {
            "null_moves_rate": float(row.null_moves_rate) if row else 0.0,
            "missing_player_rate": float(row.missing_player_rate) if row else 0.0,
            "missing_result_rate": float(row.missing_result_rate) if row else 0.0
        }

    async def _get_opening_name(self, eco_code: str) -> str:
        """Get opening name from ECO code."""
        # For now, just return the ECO code since we don't have the openings table
        return eco_code

    async def get_player_performance(
        self,
        player_id: int,
        time_range: str = "monthly"
    ) -> Dict[str, Any]:
        """Get performance statistics for a player over time."""
        try:
            # Calculate date range based on time range
            date_trunc = {
                "daily": "day",
                "weekly": "week",
                "monthly": "month",
                "yearly": "year"
            }.get(time_range, "month")

            query = f"""
                WITH time_periods AS (
                    SELECT
                        date_trunc('{date_trunc}', date) as period,
                        COUNT(*) as games_played,
                        COUNT(CASE WHEN 
                            (white_player_id = :player_id AND result = '1-0') OR
                            (black_player_id = :player_id AND result = '0-1')
                        THEN 1 END) as wins,
                        COUNT(CASE WHEN result = '1/2-1/2' THEN 1 END) as draws,
                        AVG(CASE 
                            WHEN white_player_id = :player_id THEN white_elo
                            WHEN black_player_id = :player_id THEN black_elo
                        END) as avg_rating
                    FROM games
                    WHERE (white_player_id = :player_id OR black_player_id = :player_id)
                    AND date IS NOT NULL
                    GROUP BY period
                    ORDER BY period DESC
                    LIMIT 12
                )
                SELECT
                    period,
                    games_played,
                    wins,
                    draws,
                    games_played - wins - draws as losses,
                    CAST((wins::float * 100 / NULLIF(games_played, 0)) AS NUMERIC(5,2)) as win_rate,
                    CAST((draws::float * 100 / NULLIF(games_played, 0)) AS NUMERIC(5,2)) as draw_rate,
                    CAST(avg_rating AS INTEGER) as avg_rating
                FROM time_periods
                ORDER BY period
            """

            result = await self.db.execute(text(query), {"player_id": player_id})
            rows = result.fetchall()

            if not rows:
                return None

            return {
                "periods": [row.period.strftime("%Y-%m-%d") for row in rows],
                "games_played": [row.games_played for row in rows],
                "wins": [row.wins for row in rows],
                "draws": [row.draws for row in rows],
                "losses": [row.losses for row in rows],
                "win_rates": [float(row.win_rate) if row.win_rate else 0.0 for row in rows],
                "draw_rates": [float(row.draw_rate) if row.draw_rate else 0.0 for row in rows],
                "ratings": [row.avg_rating if row.avg_rating else None for row in rows]
            }

        except Exception as e:
            logger.error(f"Error in get_player_performance: {str(e)}")
            raise

    async def get_player_openings(
        self,
        player_id: int,
        min_games: int = 5
    ) -> Dict[str, Any]:
        """Get opening statistics for a player."""
        try:
            query = """
                WITH player_openings AS (
                    SELECT
                        eco,
                        COUNT(*) as games_played,
                        COUNT(CASE WHEN 
                            (white_player_id = :player_id AND result = '1-0') OR
                            (black_player_id = :player_id AND result = '0-1')
                        THEN 1 END) as wins,
                        COUNT(CASE WHEN result = '1/2-1/2' THEN 1 END) as draws,
                        COUNT(CASE WHEN white_player_id = :player_id THEN 1 END) as white_games,
                        COUNT(CASE WHEN black_player_id = :player_id THEN 1 END) as black_games
                    FROM games
                    WHERE (white_player_id = :player_id OR black_player_id = :player_id)
                    AND eco IS NOT NULL
                    GROUP BY eco
                    HAVING COUNT(*) >= :min_games
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                )
                SELECT
                    o.*,
                    o.games_played - o.wins - o.draws as losses,
                    CAST((o.wins::float * 100 / NULLIF(o.games_played, 0)) AS NUMERIC(5,2)) as win_rate,
                    CAST((o.draws::float * 100 / NULLIF(o.games_played, 0)) AS NUMERIC(5,2)) as draw_rate
                FROM player_openings o
                ORDER BY o.games_played DESC, win_rate DESC
            """

            result = await self.db.execute(
                text(query),
                {"player_id": player_id, "min_games": min_games}
            )
            rows = result.fetchall()

            if not rows:
                return None

            openings = []
            for row in rows:
                opening_name = await self._get_opening_name(row.eco)
                openings.append({
                    "eco": row.eco,
                    "name": opening_name,
                    "games_played": row.games_played,
                    "wins": row.wins,
                    "draws": row.draws,
                    "losses": row.losses,
                    "win_rate": float(row.win_rate) if row.win_rate else 0.0,
                    "draw_rate": float(row.draw_rate) if row.draw_rate else 0.0,
                    "white_games": row.white_games,
                    "black_games": row.black_games
                })

            return {
                "openings": openings,
                "total_games": sum(o["games_played"] for o in openings),
                "total_wins": sum(o["wins"] for o in openings),
                "total_draws": sum(o["draws"] for o in openings),
                "total_losses": sum(o["losses"] for o in openings)
            }

        except Exception as e:
            logger.error(f"Error in get_player_openings: {str(e)}")
            raise