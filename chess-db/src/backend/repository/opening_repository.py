"""
Repository functions for opening analysis with improved database design support.
"""

from typing import List, Optional, Dict
from datetime import date, datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

from .models.opening import (
    OpeningStats,
    OpeningAnalysisResponse,
    PopularOpeningStats,
    AnalysisInsight as OpeningAnalysisInsight,
    OpeningVariationStats,
    OpeningComplexityStats,
    TrendData
)

logger = logging.getLogger(__name__)

async def get_player_openings(
    db: AsyncSession,
    player_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_games: int = 0,
    limit: Optional[int] = 10
) -> OpeningAnalysisResponse:
    """Get detailed opening statistics for a specific player."""
    try:
        # Build date conditions
        date_conditions = []
        if start_date:
            date_conditions.append(f"pos.last_played::date >= '{start_date}'")
        if end_date:
            date_conditions.append(f"pos.last_played::date <= '{end_date}'")
        
        date_where_clause = " AND ".join(date_conditions) if date_conditions else "TRUE"
        limit_clause = f"LIMIT {limit}" if limit else ""

        # Get opening stats from materialized view
        query = f"""
        WITH opening_stats AS (
            SELECT 
                pos.*,
                o.name as opening_name,
                o.eco as eco_code,
                COALESCE(
                    (
                        SELECT jsonb_build_object(
                            'complexity_score', 
                            (AVG(gom.game_move_length::numeric))::numeric(10,2)
                        )
                        FROM game_opening_matches gom
                        WHERE gom.opening_id = o.id
                        GROUP BY gom.opening_id
                        LIMIT 1
                    ),
                    jsonb_build_object('complexity_score', NULL)
                ) as complexity_stats
            FROM player_opening_stats pos
            JOIN openings o ON o.id = pos.opening_id
            WHERE pos.player_id = {player_id}
            AND pos.total_games >= {min_games}
            AND {date_where_clause}
            ORDER BY pos.total_games DESC
            {limit_clause}
        )
        SELECT 
            os.*,
            SUM(total_games) OVER () as total_games_all,
            SUM(wins) OVER () as total_wins,
            SUM(draws) OVER () as total_draws,
            SUM(losses) OVER () as total_losses,
            (AVG(avg_game_length) OVER ())::numeric(10,2) as overall_avg_moves
        FROM opening_stats os
        """

        result = await db.execute(text(query))
        rows = result.fetchall()

        if not rows:
            return OpeningAnalysisResponse(
                analysis=[],
                total_openings=0,
                avg_game_length=0.0,
                total_games=0,
                total_wins=0,
                total_draws=0,
                total_losses=0,
                most_successful="No openings found",
                most_played="No openings found",
                trend_data=TrendData(months=[], games=[], win_rates=[])
            )

        analysis = []
        for row in rows:
            # Process trend data
            trend_data = row.trend_data or {}
            
            # Process complexity stats
            complexity_stats = row.complexity_stats or {}
            
            analysis.append(OpeningStats(
                opening_name=row.opening_name,
                eco_code=row.eco_code,
                total_games=row.total_games,
                wins=row.wins,
                draws=row.draws,
                losses=row.losses,
                win_rate=row.win_rate,
                avg_game_length=row.avg_game_length,
                games_as_white=row.white_games,
                games_as_black=row.black_games,
                last_played=row.last_played,
                trend_data=TrendData(**process_trend_data(trend_data)),
                complexity_stats=OpeningComplexityStats(
                    avg_time_per_move=None,  # Not available in current schema
                    complexity_score=complexity_stats.get('complexity_score')
                )
            ))

        # Calculate summary statistics
        stats_summary = calculate_opening_stats_summary(analysis)
        
        return OpeningAnalysisResponse(
            analysis=analysis,
            total_openings=len(analysis),
            avg_game_length=rows[0].overall_avg_moves,
            total_games=rows[0].total_games_all,
            total_wins=rows[0].total_wins,
            total_draws=rows[0].total_draws,
            total_losses=rows[0].total_losses,
            most_successful=stats_summary['most_successful'],
            most_played=stats_summary['most_played'],
            trend_data=stats_summary['trend_data']
        )

    except Exception as e:
        logger.error(f"Error getting player opening analysis: {str(e)}")
        raise

async def get_popular_openings(
    db: AsyncSession,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_games: int = 100,
    limit: Optional[int] = 10
) -> List[PopularOpeningStats]:
    """Get statistics for popular chess openings."""
    try:
        query = f"""
        WITH game_stats AS (
            SELECT 
                o.id as opening_id,
                o.name,
                o.eco as eco_code,
                COUNT(DISTINCT g.id) as total_games,
                COUNT(DISTINCT g.white_player_id) + COUNT(DISTINCT g.black_player_id) as unique_players,
                (AVG(gom.game_move_length))::numeric(10,2) as avg_game_length,
                (AVG(gom.opening_move_length))::numeric(10,2) as avg_opening_length,
                (COUNT(*) FILTER (WHERE g.result = '1-0')::numeric * 100 / NULLIF(COUNT(*)::numeric, 0))::numeric(10,2) as white_win_rate,
                (COUNT(*) FILTER (WHERE g.result = '1/2-1/2')::numeric * 100 / NULLIF(COUNT(*)::numeric, 0))::numeric(10,2) as draw_rate,
                (AVG(gom.game_move_length::numeric))::numeric(10,2) as complexity_score
            FROM openings o
            JOIN game_opening_matches gom ON o.id = gom.opening_id
            JOIN games g ON g.id = gom.game_id
            WHERE (:start_date::date IS NULL OR g.date >= '{start_date}')
            AND (:end_date::date IS NULL OR g.date <= '{end_date}')
            GROUP BY o.id, o.name, o.eco
            HAVING COUNT(DISTINCT g.id) >= {min_games}
            ORDER BY COUNT(DISTINCT g.id) DESC
            LIMIT {limit}
        )
        SELECT *
        FROM game_stats
        """
        
        result = await db.execute(text(query))
        
        rows = result.fetchall()
        return [
            PopularOpeningStats(
                name=row.name,
                eco_code=row.eco_code,
                total_games=row.total_games,
                unique_players=row.unique_players,
                avg_game_length=row.avg_game_length,
                avg_opening_length=row.avg_opening_length,
                complexity_score=row.complexity_score,
                white_win_rate=row.white_win_rate,
                draw_rate=row.draw_rate
            )
            for row in rows
        ]

    except Exception as e:
        logger.error(f"Error getting popular openings: {str(e)}")
        raise

def process_trend_data(trend_data: Dict) -> Dict:
    """Process trend data from the database into a structured format."""
    months = trend_data.get('months', [])
    monthly_stats = trend_data.get('monthly_stats', {})
    
    return {
        'months': months,
        'games': [monthly_stats.get(m, {}).get('games', 0) for m in months],
        'win_rates': [monthly_stats.get(m, {}).get('win_rate', 0.0) for m in months]
    }

def calculate_opening_stats_summary(analysis: List[OpeningStats]) -> Dict:
    """Calculate summary statistics from opening analysis."""
    if not analysis:
        return {
            'most_successful': "No openings found",
            'most_played': "No openings found",
            'trend_data': TrendData(months=[], games=[], win_rates=[])
        }

    # Find most successful and most played openings
    most_successful = max(analysis, key=lambda x: x.win_rate).opening_name
    most_played = max(analysis, key=lambda x: x.total_games).opening_name

    # Calculate overall trend data
    all_months = set()
    monthly_games = {}
    monthly_win_rates = {}

    for stats in analysis:
        trend_info = stats.trend_data
        for i, month in enumerate(trend_info.months):
            all_months.add(month)
            monthly_games[month] = monthly_games.get(month, 0) + trend_info.games[i]
            if month not in monthly_win_rates:
                monthly_win_rates[month] = []
            monthly_win_rates[month].append((trend_info.win_rates[i], trend_info.games[i]))

    sorted_months = sorted(all_months, reverse=True)[:6]
    monthly_avg_win_rates = []
    
    for month in sorted_months:
        if month in monthly_win_rates:
            total_games = sum(games for _, games in monthly_win_rates[month])
            weighted_win_rate = sum(rate * games for rate, games in monthly_win_rates[month]) / total_games if total_games > 0 else 0
            monthly_avg_win_rates.append(round(weighted_win_rate, 2))
        else:
            monthly_avg_win_rates.append(0.0)

    return {
        'most_successful': most_successful,
        'most_played': most_played,
        'trend_data': TrendData(
            months=sorted_months,
            games=[monthly_games.get(m, 0) for m in sorted_months],
            win_rates=monthly_avg_win_rates
        )
    }
