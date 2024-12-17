"""
Repository functions for opening analysis.
"""

from typing import List, Optional, Tuple
from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import json

from .models.opening import (
    OpeningStats,
    OpeningAnalysisResponse,
    PopularOpeningStats,
    AnalysisInsight as OpeningAnalysisInsight,
    OpeningVariationStats,
    TrendData
)

async def get_player_openings(
    db: AsyncSession,
    username: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_games: int = 0,
    limit: Optional[int] = 10
) -> OpeningAnalysisResponse:
    """Get opening statistics for a specific player."""
    
    # Build date conditions
    date_conditions = []
    if start_date:
        # Ensure date is in UTC and properly formatted
        date_conditions.append(f"g.date::date >= DATE('{start_date}')")
    if end_date:
        # Ensure date is in UTC and properly formatted
        date_conditions.append(f"g.date::date <= DATE('{end_date}')")
    
    date_where_clause = " AND ".join(date_conditions) if date_conditions else "TRUE"
    
    # First check if we have any openings that meet the criteria
    count_query = f"""
    SELECT COUNT(*) 
    FROM (
        SELECT o.id
        FROM games pg
        JOIN game_opening_matches gom ON pg.id = gom.game_id
        JOIN openings o ON gom.opening_id = o.id
        WHERE (pg.white_player_id::text = :username OR pg.black_player_id::text = :username)
        AND {date_where_clause}
        GROUP BY o.id
        HAVING COUNT(DISTINCT pg.id) >= :min_games
    ) filtered_openings
    """
    
    count_result = await db.execute(text(count_query), {"username": username, "min_games": min_games})
    count_row = count_result.fetchone()
    if not count_row or count_row[0] == 0:
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

    # Get total stats for all games within date range
    total_query = f"""
    WITH player_games AS (
        SELECT g.*, gom.opening_id, gom.game_move_length
        FROM games g
        JOIN game_opening_matches gom ON g.id = gom.game_id
        WHERE (g.white_player_id::text = :username OR g.black_player_id::text = :username)
        AND {date_where_clause}
    )
    SELECT 
        COUNT(DISTINCT id) as total_games,
        COUNT(DISTINCT opening_id) as total_openings,
        SUM(CASE 
            WHEN result = '1-0' AND white_player_id::text = :username OR 
                 result = '0-1' AND black_player_id::text = :username THEN 1 
            ELSE 0 
        END) as total_wins,
        SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as total_draws,
        SUM(CASE 
            WHEN (result = '1-0' AND black_player_id::text = :username) OR 
                 (result = '0-1' AND white_player_id::text = :username) THEN 1 
            ELSE 0 
        END) as total_losses,
        AVG(game_move_length) as avg_game_length
    FROM player_games
    """
    
    # print(f"Executing total query:\n{total_query}")
    
    total_result = await db.execute(text(total_query), {"username": username})
    total_row = total_result.fetchone()
    
    # Log the total stats for debugging
    print(f"Total stats: Games: {total_row.total_games}, Openings: {total_row.total_openings}, Win Rate: {(total_row.total_wins / total_row.total_games * 100):.2f}%")
    
    # Create a CTE for filtered stats and trend data
    opening_query = f"""
    WITH recent_months AS (
        SELECT DISTINCT TO_CHAR(date, 'YYYY-MM') as month
        FROM games
        WHERE (white_player_id::text = :username OR black_player_id::text = :username)
        AND {date_where_clause}
        ORDER BY month DESC
        LIMIT 6
    ),
    monthly_stats AS (
        SELECT 
            o.name as opening_name,
            rm.month,
            COUNT(DISTINCT pg.id) as games_in_month,
            ROUND(100.0 * 
                SUM(CASE WHEN 
                    (pg.white_player_id::text = :username AND pg.result = '1-0') OR 
                    (pg.black_player_id::text = :username AND pg.result = '0-1')
                THEN 1 ELSE 0 END)::decimal / 
                NULLIF(COUNT(DISTINCT pg.id), 0),
                1
            ) as win_rate_in_month
        FROM games pg
        JOIN game_opening_matches gom ON pg.id = gom.game_id
        JOIN openings o ON gom.opening_id = o.id
        CROSS JOIN recent_months rm
        WHERE (pg.white_player_id::text = :username OR pg.black_player_id::text = :username)
        AND {date_where_clause}
        AND TO_CHAR(pg.date, 'YYYY-MM') = rm.month
        GROUP BY o.name, rm.month
    ),
    overall_monthly_stats AS (
        SELECT 
            rm.month,
            COUNT(DISTINCT pg.id) as games_in_month,
            ROUND(100.0 * 
                SUM(CASE WHEN 
                    (pg.white_player_id::text = :username AND pg.result = '1-0') OR 
                    (pg.black_player_id::text = :username AND pg.result = '0-1')
                THEN 1 ELSE 0 END)::decimal / 
                NULLIF(COUNT(DISTINCT pg.id), 0),
                1
            ) as win_rate_in_month
        FROM games pg
        JOIN game_opening_matches gom ON pg.id = gom.game_id
        CROSS JOIN recent_months rm
        WHERE (pg.white_player_id::text = :username OR pg.black_player_id::text = :username)
        AND {date_where_clause}
        AND TO_CHAR(pg.date, 'YYYY-MM') = rm.month
        GROUP BY rm.month
        ORDER BY rm.month DESC
    ),
    filtered_stats AS (
        SELECT 
            o.name as opening_name,
            COUNT(DISTINCT pg.id) as total_games,
            SUM(CASE WHEN 
                (pg.white_player_id::text = :username AND pg.result = '1-0') OR 
                (pg.black_player_id::text = :username AND pg.result = '0-1')
            THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN pg.result = '1/2-1/2' THEN 1 ELSE 0 END) as draws,
            SUM(CASE WHEN 
                (pg.white_player_id::text = :username AND pg.result = '0-1') OR 
                (pg.black_player_id::text = :username AND pg.result = '1-0')
            THEN 1 ELSE 0 END) as losses,
            ROUND(100.0 * SUM(CASE WHEN 
                (pg.white_player_id::text = :username AND pg.result = '1-0') OR 
                (pg.black_player_id::text = :username AND pg.result = '0-1')
            THEN 1 ELSE 0 END)::decimal / NULLIF(COUNT(DISTINCT pg.id), 0), 1) as win_rate,
            SUM(CASE WHEN pg.white_player_id::text = :username THEN 1 ELSE 0 END) as games_as_white,
            SUM(CASE WHEN pg.black_player_id::text = :username THEN 1 ELSE 0 END) as games_as_black,
            ROUND(AVG(
                CASE 
                    WHEN pg.moves IS NOT NULL THEN 
                        (get_byte(pg.moves::bytea, 0) << 8 | get_byte(pg.moves::bytea, 1))::integer
                    ELSE NULL 
                END
            ), 1) as avg_game_length,
            json_build_object(
                'months', COALESCE((
                    SELECT json_agg(ms.month ORDER BY ms.month DESC)
                    FROM monthly_stats ms
                    WHERE ms.opening_name = o.name
                ), '[]'::json),
                'games', COALESCE((
                    SELECT json_agg(COALESCE(ms.games_in_month, 0) ORDER BY ms.month DESC)
                    FROM monthly_stats ms
                    WHERE ms.opening_name = o.name
                ), '[]'::json),
                'win_rates', COALESCE((
                    SELECT json_agg(COALESCE(ms.win_rate_in_month, 0) ORDER BY ms.month DESC)
                    FROM monthly_stats ms
                    WHERE ms.opening_name = o.name
                ), '[]'::json)
            )::json as trend_data
        FROM games pg
        JOIN game_opening_matches gom ON pg.id = gom.game_id
        JOIN openings o ON gom.opening_id = o.id
        WHERE (pg.white_player_id::text = :username OR pg.black_player_id::text = :username)
        AND {date_where_clause}
        GROUP BY o.name
        HAVING COUNT(DISTINCT pg.id) >= :min_games
    )
    SELECT 
        o.opening_name,
        o.total_games,
        o.wins,
        o.draws,
        o.losses,
        o.win_rate,
        o.games_as_white,
        o.games_as_black,
        o.avg_game_length,
        o.trend_data,
        s.most_successful,
        s.most_played,
        s.avg_game_length as overall_avg_game_length,
        s.total_openings,
        s.total_games as overall_total_games,
        s.total_wins,
        s.total_draws,
        s.total_losses,
        s.trend_data as overall_trend_data
    FROM filtered_stats o
    CROSS JOIN (
        SELECT 
            (
                SELECT opening_name 
                FROM filtered_stats 
                ORDER BY win_rate DESC, total_games DESC 
                LIMIT 1
            ) as most_successful,
            (
                SELECT opening_name 
                FROM filtered_stats 
                ORDER BY total_games DESC, win_rate DESC 
                LIMIT 1
            ) as most_played,
            ROUND(AVG(NULLIF(avg_game_length, 0)), 1) as avg_game_length,
            COUNT(*) as total_openings,
            COALESCE((SELECT SUM(total_games) FROM filtered_stats), 0) as total_games,
            COALESCE((SELECT SUM(wins) FROM filtered_stats), 0) as total_wins,
            COALESCE((SELECT SUM(draws) FROM filtered_stats), 0) as total_draws,
            COALESCE((SELECT SUM(losses) FROM filtered_stats), 0) as total_losses,
            json_build_object(
                'months', COALESCE((
                    SELECT json_agg(month ORDER BY month DESC)
                    FROM overall_monthly_stats
                ), '[]'::json),
                'games', COALESCE((
                    SELECT json_agg(COALESCE(games_in_month, 0) ORDER BY month DESC)
                    FROM overall_monthly_stats
                ), '[]'::json),
                'win_rates', COALESCE((
                    SELECT json_agg(COALESCE(win_rate_in_month, 0) ORDER BY month DESC)
                    FROM overall_monthly_stats
                ), '[]'::json)
            )::json as trend_data
        FROM filtered_stats
    ) s
    ORDER BY o.total_games DESC
    """
    
    # Debug: Print the query
    print(f"Executing query:\n{opening_query}")
    
    if limit is not None:
        opening_query += f"\nLIMIT NULLIF(:limit, 0)"
    
    opening_result = await db.execute(text(opening_query), {"username": username, "min_games": min_games, "limit": limit})
    opening_rows = opening_result.mappings().all()
    
    if not opening_rows:
        return OpeningAnalysisResponse()

    # Create OpeningStats objects for each opening
    openings = []
    for row in opening_rows:
        trend_data = row['trend_data']
        if not isinstance(trend_data, dict):
            trend_data = {}
            
        trend_data_json = json.dumps({
            "months": trend_data.get('months', []),
            "games": trend_data.get('games', []),
            "win_rates": trend_data.get('win_rates', [])
        })

        opening_stats = OpeningStats(
            opening_name=row['opening_name'],
            total_games=row['total_games'],
            win_count=row['wins'],
            draw_count=row['draws'],
            loss_count=row['losses'],
            win_rate=row['win_rate'],
            games_as_white=row['games_as_white'],
            games_as_black=row['games_as_black'],
            avg_game_length=row['avg_game_length'],
            trend_data=trend_data_json,
            message=generate_opening_message(row),
            type="opening"
        )
        openings.append(opening_stats)

    # Extract overall trend data
    overall_trend_data = opening_rows[0]['overall_trend_data'] if opening_rows else {}
    if not isinstance(overall_trend_data, dict):
        overall_trend_data = {}

    # Create the response object
    response = OpeningAnalysisResponse(
        analysis=openings,
        total_openings=opening_rows[0]['total_openings'] if opening_rows else 0,
        avg_game_length=opening_rows[0]['avg_game_length'] if opening_rows else 0.0,
        total_games=opening_rows[0]['total_games'] if opening_rows else 0,
        total_wins=opening_rows[0]['total_wins'] if opening_rows else 0,
        total_draws=opening_rows[0]['total_draws'] if opening_rows else 0,
        total_losses=opening_rows[0]['total_losses'] if opening_rows else 0,
        most_successful=opening_rows[0]['most_successful'] if opening_rows else "No openings found",
        most_played=opening_rows[0]['most_played'] if opening_rows else "No openings found",
        trend_data=json.dumps({
            "months": overall_trend_data.get('months', []),
            "games": overall_trend_data.get('games', []),
            "win_rates": overall_trend_data.get('win_rates', [])
        })
    )

    return response

def generate_opening_message(stats: dict) -> str:
    """Generate an insight message for an opening."""
    win_rate = stats['win_rate']
    total_games = stats['total_games']
    games_as_white = stats['games_as_white']
    games_as_black = stats['games_as_black']
    
    # Base message about frequency
    message = f"Played {total_games} times"
    if games_as_white > games_as_black:
        message += f" ({games_as_white} as White, {games_as_black} as Black)"
    elif games_as_black > games_as_white:
        message += f" ({games_as_black} as Black, {games_as_white} as White)"
    
    # Add performance insight
    if win_rate >= 70:
        message += f". Exceptional performance with {win_rate:.1f}% win rate"
    elif win_rate >= 55:
        message += f". Strong performance with {win_rate:.1f}% win rate"
    elif win_rate >= 45:
        message += f". Balanced performance with {win_rate:.1f}% win rate"
    else:
        message += f". Challenging opening with {win_rate:.1f}% win rate"
    
    return message

async def get_popular_openings(
    db: AsyncSession,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_games: int = 100,
    limit: Optional[int] = 10
) -> List[PopularOpeningStats]:
    """Get statistics for popular chess openings."""
    
    # Convert dates to strings or 'null' if None
    start_date_str = f"'{start_date}'" if start_date else 'null'
    end_date_str = f"'{end_date}'" if end_date else 'null'
    
    query = f"""
    WITH game_stats AS (
        SELECT 
            o.name,
            COUNT(DISTINCT g.id) as total_games,
            COUNT(DISTINCT g.white_player_id) + COUNT(DISTINCT g.black_player_id) as unique_players,
            (SUM(CASE WHEN g.result = '1-0' THEN 1 ELSE 0 END)::float * 100 / 
                NULLIF(COUNT(*), 0))::numeric(5,2) as white_win_rate
        FROM games g
        JOIN game_opening_matches gom ON g.id = gom.game_id
        JOIN openings o ON o.id = gom.opening_id
        WHERE ({start_date_str}::timestamp IS NULL OR g.date::date >= {start_date_str}::timestamp)
        AND ({end_date_str}::timestamp IS NULL OR g.date::date <= {end_date_str}::timestamp)
        GROUP BY o.name
        HAVING COUNT(DISTINCT g.id) >= {min_games}
    )
    SELECT *
    FROM game_stats
    ORDER BY total_games DESC
    """
    
    if limit:
        query += f"\nLIMIT NULLIF({limit}, 0)"
    
    result = await db.execute(text(query))
    rows = result.fetchall()
    
    return [
        PopularOpeningStats(
            name=row.name,
            total_games=row.total_games,
            white_win_rate=row.white_win_rate,
            unique_players=row.unique_players,
            variations=[]  # We'll add variations later if needed
        )
        for row in rows
    ]
