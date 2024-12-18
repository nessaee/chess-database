from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, text, func
import logging
from datetime import datetime, timedelta

from ..models import (
    PlayerDB,
    PlayerResponse,
    PlayerSearchResponse,
    PlayerPerformanceResponse,
    DetailedPerformanceResponse
)
from ..common.validation import DateHandler
from ..game.decoder import GameDecoder

logger = logging.getLogger(__name__)

class PlayerRepository:
    """Repository for managing chess player data and analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.date_handler = DateHandler()
        self.game_decoder = GameDecoder()

    async def search_players(
        self,
        query: str,
        limit: int = 10
    ) -> List[PlayerSearchResponse]:
        """
        Search for players by name.
        
        Args:
            query: Search string to match against player names
            limit: Maximum number of results to return
            
        Returns:
            List of PlayerSearchResponse objects with name and rating
        """
        try:
            search_query = (
                select(PlayerDB.id, PlayerDB.name)
                .where(PlayerDB.name.ilike(f'%{query}%'))
                .order_by(PlayerDB.name)
                .limit(limit)
            )

            result = await self.db.execute(search_query)
            players = result.all()
            
            return [
                PlayerSearchResponse(
                    id=player.id,
                    name=player.name,
                )
                for player in players
            ]

        except Exception as e:
            logger.error(f"Error in search_players: {str(e)}")
            raise

    async def get_player_by_name(self, name: str) -> Optional[PlayerDB]:
        """
        Get a player by their exact name.
        
        Args:
            name: The exact name of the player to find
            
        Returns:
            PlayerDB object if found, None otherwise
        """
        try:
            query = select(PlayerDB).where(PlayerDB.name == name)
            result = await self.db.execute(query)
            player = result.scalar_one_or_none()
            return player
        except Exception as e:
            logger.error(f"Error getting player by name: {e}")
            return None

    async def get_player_performance(
        self,
        player_id: int,
        time_range: str = "monthly",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[DetailedPerformanceResponse]:
        """
        Get detailed performance metrics for a player.
        
        Args:
            player_id: ID of the player to analyze
            time_range: Time grouping ('daily', 'weekly', 'monthly', 'yearly')
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)
            
        Returns:
            List of DetailedPerformanceResponse objects with metrics per time period
        """
        try:
            logger.info(f"Getting performance for player {player_id} from {start_date} to {end_date}")
            
            # First verify the player exists
            player_result = await self.db.execute(
                select(PlayerDB).where(PlayerDB.id == player_id)
            )
            player = player_result.scalar_one_or_none()
            if not player:
                logger.error(f"Player {player_id} not found")
                return []
            
            # Validate dates
            try:
                start_date = self.date_handler.validate_and_parse_date(start_date, "start_date")
                end_date = self.date_handler.validate_and_parse_date(end_date, "end_date")
                logger.info(f"Validated dates: start={start_date}, end={end_date}")
            except Exception as e:
                logger.error(f"Date validation error: {str(e)}")
                raise

            # Convert None dates to NULL for SQL
            sql_start_date = "NULL" if start_date is None else f"'{start_date}'"
            sql_end_date = "NULL" if end_date is None else f"'{end_date}'"
            logger.info(f"SQL dates: start={sql_start_date}, end={sql_end_date}")

            # Determine time grouping format
            time_format = {
                "daily": "YYYY-MM-DD",
                "weekly": "YYYY-WW",
                "monthly": "YYYY-MM",
                "yearly": "YYYY"
            }.get(time_range, "YYYY-MM")

            query = f"""
                WITH player_games AS (
                    SELECT 
                        g.*,
                        to_char(g.date, '{time_format}') as period,
                        CASE 
                            WHEN g.white_player_id = {player_id} THEN 'white'
                            ELSE 'black'
                        END as player_color,
                        CASE
                            WHEN (g.white_player_id = {player_id} AND g.result = '1-0')
                                OR (g.black_player_id = {player_id} AND g.result = '0-1')
                            THEN 1
                            WHEN g.result = '1/2-1/2' THEN 0.5
                            ELSE 0
                        END as points,
                        octet_length(moves) / 2 as num_moves,
                        CASE 
                            WHEN g.white_player_id = {player_id} THEN g.white_elo
                            ELSE g.black_elo
                        END as player_elo
                    FROM games g
                    WHERE (g.white_player_id = {player_id} OR g.black_player_id = {player_id})
                    AND CASE 
                        WHEN {sql_start_date} IS NULL THEN true 
                        ELSE g.date >= {sql_start_date}::date 
                    END
                    AND CASE 
                        WHEN {sql_end_date} IS NULL THEN true 
                        ELSE g.date <= {sql_end_date}::date 
                    END
                ),
                period_stats AS (
                    SELECT 
                        period,
                        COUNT(*) as games_played,
                        SUM(CASE WHEN points = 1 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN points = 0 THEN 1 ELSE 0 END) as losses,
                        SUM(CASE WHEN points = 0.5 THEN 1 ELSE 0 END) as draws,
                        AVG(num_moves) as avg_moves,
                        SUM(CASE WHEN player_color = 'white' THEN 1 ELSE 0 END) as white_games,
                        SUM(CASE WHEN player_color = 'black' THEN 1 ELSE 0 END) as black_games,
                        COUNT(DISTINCT o.name) as unique_openings,
                        AVG(player_elo) as avg_elo,
                        MAX(player_elo) - MIN(player_elo) as elo_change
                    FROM player_games pg
                    JOIN game_opening_matches gom ON pg.id = gom.game_id
                    JOIN openings o ON gom.opening_id = o.id
                    GROUP BY period
                    ORDER BY period
                )
                SELECT 
                    period,
                    games_played,
                    wins,
                    losses,
                    draws,
                    ROUND(100.0 * (wins + 0.5 * draws) / NULLIF(games_played, 0), 2) as win_rate,
                    ROUND(COALESCE(avg_moves, 0)::numeric, 2) as avg_moves,
                    white_games,
                    black_games,
                    unique_openings,
                    ROUND(COALESCE(unique_openings::numeric / NULLIF(games_played, 0), 0), 2) as opening_diversity,
                    ROUND(avg_elo::numeric, 0) as avg_elo,
                    ROUND(elo_change::numeric, 0) as elo_change
                FROM period_stats
            """

            logger.info("Executing performance query")
            try:
                result = await self.db.execute(text(query))
                rows = result.fetchall()
                logger.info(f"Found {len(rows)} performance records")
            except Exception as e:
                logger.error(f"Error executing query: {str(e)}")
                logger.error(f"Query was: {query}")
                raise

            return [
                DetailedPerformanceResponse(
                    time_period=row.period,
                    games_played=row.games_played,
                    wins=row.wins,
                    losses=row.losses,
                    draws=row.draws,
                    win_rate=row.win_rate or 0,
                    avg_moves=row.avg_moves or 0,
                    white_games=row.white_games,
                    black_games=row.black_games,
                    avg_elo=row.avg_elo,
                    elo_change=row.elo_change,
                    opening_diversity=row.opening_diversity or 0,
                    avg_game_length=row.avg_moves or 0
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error getting player performance: {str(e)}")
            logger.exception(e)  # This will log the full stack trace
            raise

    async def get_detailed_stats(
        self,
        player_id: int,
        time_period: Optional[str] = None
    ) -> Optional[DetailedPerformanceResponse]:
        """
        Get detailed statistics for a player.
        
        Args:
            player_id: ID of the player
            time_period: Optional time period filter (e.g., '1y', '6m', '3m', '1m')
            
        Returns:
            DetailedPerformanceResponse with aggregated statistics
        """
        try:
            # Convert time_period to date range
            start_date = None
            end_date = None
            if time_period:
                end_date = datetime.now().date()
                if time_period == '1y':
                    start_date = end_date - timedelta(days=365)
                elif time_period == '6m':
                    start_date = end_date - timedelta(days=180)
                elif time_period == '3m':
                    start_date = end_date - timedelta(days=90)
                elif time_period == '1m':
                    start_date = end_date - timedelta(days=30)

            # Get performance data
            performance_data = await self.get_player_performance(
                player_id=player_id,
                time_range='monthly',
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None
            )

            if not performance_data:
                return None

            # Aggregate the data
            total_games = sum(p.games_played for p in performance_data)
            total_wins = sum(p.wins for p in performance_data)
            total_losses = sum(p.losses for p in performance_data)
            total_draws = sum(p.draws for p in performance_data)
            
            # Calculate aggregated metrics
            win_rate = round(100.0 * (total_wins + 0.5 * total_draws) / total_games, 2) if total_games > 0 else 0
            avg_moves = round(sum(p.avg_moves * p.games_played for p in performance_data) / total_games, 2) if total_games > 0 else 0
            
            return DetailedPerformanceResponse(
                time_period=time_period or 'all',
                games_played=total_games,
                wins=total_wins,
                losses=total_losses,
                draws=total_draws,
                win_rate=win_rate,
                avg_moves=avg_moves,
                white_games=sum(p.white_games for p in performance_data),
                black_games=sum(p.black_games for p in performance_data),
                avg_elo=None,  # We'll add this if needed
                elo_change=None,  # We'll add this if needed
                opening_diversity=None,  # We'll add this if needed
                avg_game_length=avg_moves
            )

        except Exception as e:
            logger.error(f"Error getting detailed stats: {str(e)}")
            raise

    async def _get_player_ratings(self, player_ids: List[int]) -> Dict[int, int]:
        """
        Get latest ELO ratings for players.
        
        Args:
            player_ids: List of player IDs to get ratings for
            
        Returns:
            Dictionary mapping player IDs to their latest ELO rating
        """
        if not player_ids:
            return {}

        query = """
            WITH latest_ratings AS (
                SELECT DISTINCT ON (player_id)
                    player_id,
                    elo_rating,
                    rating_date
                FROM player_ratings
                WHERE player_id = ANY(:player_ids)
                ORDER BY player_id, rating_date DESC
            )
            SELECT player_id, elo_rating
            FROM latest_ratings
        """

        try:
            result = await self.db.execute(text(query), {"player_ids": player_ids})
            return {row.player_id: row.elo_rating for row in result}
        except Exception:
            logger.warning("Error fetching player ratings", exc_info=True)
            return {}

    async def _get_period_elo_ratings(
        self,
        player_id: int,
        time_range: str,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> Dict[str, Dict[str, int]]:
        """
        Get ELO ratings for each time period.
        
        Args:
            player_id: ID of the player to get ratings for
            time_range: Time grouping ('daily', 'weekly', 'monthly', 'yearly')
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)
            
        Returns:
            Dictionary mapping time periods to ELO rating stats
        """
        try:
            time_format = {
                "daily": "YYYY-MM-DD",
                "weekly": "YYYY-WW",
                "monthly": "YYYY-MM",
                "yearly": "YYYY"
            }.get(time_range, "YYYY-MM")

            query = f"""
                WITH period_ratings AS (
                    SELECT 
                        to_char(rating_date, '{time_format}') as period,
                        AVG(elo_rating) as avg_elo,
                        MAX(elo_rating) - MIN(elo_rating) as elo_change
                    FROM player_ratings
                    WHERE player_id = {player_id}
                    AND ('{start_date}'::date IS NULL OR rating_date >= '{start_date}'::date)
                    AND ('{end_date}'::date IS NULL OR rating_date <= '{end_date}'::date)
                    GROUP BY to_char(rating_date, '{time_format}')
                )
                SELECT period, avg_elo, elo_change
                FROM period_ratings
                ORDER BY period
            """

            result = await self.db.execute(text(query))

            return {
                row.period: {
                    'avg_elo': int(row.avg_elo),
                    'elo_change': int(row.elo_change)
                }
                for row in result
            }

        except Exception:
            logger.warning("Error fetching period ELO ratings", exc_info=True)
            return {}