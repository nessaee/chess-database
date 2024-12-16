from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, text, func
import logging
from datetime import datetime

from ..models import (
    PlayerDB,
    PlayerResponse,
    PlayerSearchResponse,
    PlayerPerformanceResponse,
    DetailedPerformanceResponse
)
from ..common.validation import DateHandler

logger = logging.getLogger(__name__)

class PlayerRepository:
    """Repository for managing chess player data and analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.date_handler = DateHandler()

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
            search_query = select(PlayerDB).filter(
                PlayerDB.name.ilike(f"%{query}%")
            ).limit(limit)

            result = await self.db.execute(search_query)
            players = result.scalars().all()

            # Get ELO ratings for players
            player_ratings = await self._get_player_ratings([p.id for p in players])

            return [
                PlayerSearchResponse(
                    id=player.id,
                    name=player.name,
                    elo=player_ratings.get(player.id)
                )
                for player in players
            ]

        except Exception as e:
            logger.error(f"Error searching players: {str(e)}")
            raise

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
            # Validate dates
            start_date = self.date_handler.validate_and_parse_date(start_date, "start_date")
            end_date = self.date_handler.validate_and_parse_date(end_date, "end_date")

            # Determine time grouping format
            time_format = {
                "daily": "YYYY-MM-DD",
                "weekly": "YYYY-WW",
                "monthly": "YYYY-MM",
                "yearly": "YYYY"
            }.get(time_range, "YYYY-MM")

            query = """
                WITH player_games AS (
                    SELECT 
                        g.*,
                        to_char(g.date, :time_format) as period,
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
                ),
                period_stats AS (
                    SELECT 
                        period,
                        COUNT(*) as games_played,
                        SUM(CASE WHEN points = 1 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN points = 0 THEN 1 ELSE 0 END) as losses,
                        SUM(CASE WHEN points = 0.5 THEN 1 ELSE 0 END) as draws,
                        AVG(array_length(string_to_array(moves, ' '), 1)) as avg_moves,
                        SUM(CASE WHEN player_color = 'white' THEN 1 ELSE 0 END) as white_games,
                        SUM(CASE WHEN player_color = 'black' THEN 1 ELSE 0 END) as black_games,
                        COUNT(DISTINCT eco) as unique_openings
                    FROM player_games
                    GROUP BY period
                    ORDER BY period
                )
                SELECT 
                    period,
                    games_played,
                    wins,
                    losses,
                    draws,
                    ROUND(100.0 * (wins + 0.5 * draws) / games_played, 2) as win_rate,
                    ROUND(avg_moves::numeric, 2) as avg_moves,
                    white_games,
                    black_games,
                    unique_openings,
                    ROUND(unique_openings::numeric / games_played, 2) as opening_diversity
                FROM period_stats
            """

            result = await self.db.execute(
                text(query),
                {
                    "player_id": player_id,
                    "time_format": time_format,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            rows = result.fetchall()

            # Get ELO ratings for the periods
            elo_data = await self._get_period_elo_ratings(player_id, time_range, start_date, end_date)

            return [
                DetailedPerformanceResponse(
                    time_period=row.period,
                    games_played=row.games_played,
                    wins=row.wins,
                    losses=row.losses,
                    draws=row.draws,
                    win_rate=row.win_rate,
                    avg_moves=row.avg_moves,
                    white_games=row.white_games,
                    black_games=row.black_games,
                    avg_elo=elo_data.get(row.period, {}).get('avg_elo'),
                    elo_change=elo_data.get(row.period, {}).get('elo_change'),
                    opening_diversity=row.opening_diversity,
                    avg_game_length=row.avg_moves
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error getting player performance: {str(e)}")
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

            query = """
                WITH period_ratings AS (
                    SELECT 
                        to_char(rating_date, :time_format) as period,
                        AVG(elo_rating) as avg_elo,
                        MAX(elo_rating) - MIN(elo_rating) as elo_change
                    FROM player_ratings
                    WHERE player_id = :player_id
                    AND (:start_date::date IS NULL OR rating_date >= :start_date::date)
                    AND (:end_date::date IS NULL OR rating_date <= :end_date::date)
                    GROUP BY to_char(rating_date, :time_format)
                )
                SELECT period, avg_elo, elo_change
                FROM period_ratings
                ORDER BY period
            """

            result = await self.db.execute(
                text(query),
                {
                    "player_id": player_id,
                    "time_format": time_format,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )

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