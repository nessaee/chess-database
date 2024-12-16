"""
Repository functions for opening analysis.
"""

from typing import List, Optional, Tuple
from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .models.opening import (
    OpeningStats,
    OpeningAnalysisResponse,
    PopularOpeningStats,
    AnalysisInsight as OpeningAnalysisInsight,
    OpeningVariationStats
)

async def get_player_openings(
    db: AsyncSession,
    username: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_games: int = 5,
    limit: int = 10
) -> OpeningAnalysisResponse:
    """Get opening statistics for a specific player."""
    
    # Convert dates to strings or 'null' if None
    start_date_str = f"'{start_date}'" if start_date else 'null'
    end_date_str = f"'{end_date}'" if end_date else 'null'
    
    # Get total stats
    total_query = f"""
    WITH player_games AS (
        SELECT g.*, gom.opening_id, gom.game_move_length
        FROM games g
        JOIN game_opening_matches gom ON g.id = gom.game_id
        WHERE (g.white_player_id::text = '{username}' OR g.black_player_id::text = '{username}')
        AND ({start_date_str}::timestamp IS NULL OR g.date >= {start_date_str}::timestamp)
        AND ({end_date_str}::timestamp IS NULL OR g.date <= {end_date_str}::timestamp)
    )
    SELECT 
        COUNT(DISTINCT id) as total_games,
        COUNT(DISTINCT opening_id) as total_openings,
        SUM(CASE 
            WHEN result = '1-0' AND white_player_id::text = '{username}' OR 
                 result = '0-1' AND black_player_id::text = '{username}' THEN 1 
            ELSE 0 
        END) as total_wins,
        SUM(CASE WHEN result = '1/2-1/2' THEN 1 ELSE 0 END) as total_draws,
        SUM(CASE 
            WHEN result = '1-0' AND black_player_id::text = '{username}' OR 
                 result = '0-1' AND white_player_id::text = '{username}' THEN 1 
            ELSE 0 
        END) as total_losses,
        AVG(game_move_length) as avg_game_length
    FROM player_games
    """
    
    print(f"Executing total query:\n{total_query}")
    
    total_result = await db.execute(text(total_query))
    total_row = total_result.fetchone()
    
    # Log the total stats for debugging
    print(f"Total stats: Games: {total_row.total_games}, Openings: {total_row.total_openings}, Win Rate: {(total_row.total_wins / total_row.total_games * 100):.2f}%")
    
    # Get all openings without limit for analysis
    all_openings_query = f"""
    WITH player_games AS (
        SELECT g.*, gom.opening_id, gom.game_move_length
        FROM games g
        JOIN game_opening_matches gom ON g.id = gom.game_id
        WHERE (g.white_player_id::text = '{username}' OR g.black_player_id::text = '{username}')
        AND ({start_date_str}::timestamp IS NULL OR g.date >= {start_date_str}::timestamp)
        AND ({end_date_str}::timestamp IS NULL OR g.date <= {end_date_str}::timestamp)
    ),
    opening_stats AS (
        SELECT 
            o.name,
            COUNT(DISTINCT pg.id) as games_played,
            SUM(CASE 
                WHEN pg.result = '1-0' AND '{username}' = pg.white_player_id::text OR 
                     pg.result = '0-1' AND '{username}' = pg.black_player_id::text THEN 1 
                ELSE 0 
            END) as wins,
            SUM(CASE WHEN pg.result = '1/2-1/2' THEN 1 ELSE 0 END) as draws,
            SUM(CASE 
                WHEN pg.result = '1-0' AND '{username}' = pg.black_player_id::text OR 
                     pg.result = '0-1' AND '{username}' = pg.white_player_id::text THEN 1 
                ELSE 0 
            END) as losses,
            SUM(CASE WHEN '{username}' = pg.white_player_id::text THEN 1 ELSE 0 END) as white_games,
            SUM(CASE WHEN '{username}' = pg.black_player_id::text THEN 1 ELSE 0 END) as black_games,
            (SUM(CASE 
                WHEN pg.result = '1-0' AND '{username}' = pg.white_player_id::text OR 
                     pg.result = '0-1' AND '{username}' = pg.black_player_id::text THEN 1 
                ELSE 0 
            END)::float * 100 / COUNT(DISTINCT pg.id))::numeric(5,2) as win_rate,
            (SUM(CASE WHEN pg.result = '1/2-1/2' THEN 1 ELSE 0 END)::float * 100 / COUNT(DISTINCT pg.id))::numeric(5,2) as draw_rate,
            array_length(string_to_array(o.name, ':'), 1) as variation_depth
        FROM player_games pg
        JOIN openings o ON o.id = pg.opening_id
        GROUP BY o.name, o.id
        HAVING COUNT(DISTINCT pg.id) >= {min_games}
    )
    SELECT *
    FROM opening_stats
    ORDER BY games_played DESC, variation_depth DESC
    """
    
    # Log the query for debugging
    print(f"Executing query:\n{all_openings_query}")
    
    all_openings_result = await db.execute(text(all_openings_query))
    all_openings_rows = all_openings_result.fetchall()
    
    # Log the results for debugging
    print(f"Found {len(all_openings_rows)} openings")
    for row in all_openings_rows:
        print(f"Opening: {row.name} (Games: {row.games_played}, Win Rate: {row.win_rate}%")
    
    all_openings = [
        OpeningStats(
            name=row.name,
            games_played=row.games_played,
            total_games=row.games_played,
            wins=row.wins,
            win_count=row.wins,
            draws=row.draws,
            draw_count=row.draws,
            losses=row.losses,
            loss_count=row.losses,
            win_rate=row.win_rate,
            draw_rate=row.draw_rate,
            white_games=row.white_games,
            black_games=row.black_games,
            variations=[]  # We'll add variations later
        )
        for row in all_openings_rows
    ]
    
    # Generate analysis insights
    analysis = []
    if total_row.total_games > 0:
        # Overall win rate insight
        win_rate = (total_row.total_wins / total_row.total_games) * 100
        
        overall_insight = OpeningAnalysisInsight(
            message=f"Overall win rate: {win_rate:.1f}%",
            type="win_rate",
            opening_name="All Openings",
            total_games=total_row.total_games,
            win_count=total_row.total_wins,
            draw_count=total_row.total_draws,
            loss_count=total_row.total_losses,
            win_rate=win_rate,
            avg_game_length=float(total_row.avg_game_length or 0),
            games_as_white=sum(o.white_games for o in all_openings),
            games_as_black=sum(o.black_games for o in all_openings),
            avg_opponent_rating=None,
            last_played=None,
            favorite_response=None,
            variations=[]
        )
        analysis.append(overall_insight.to_dict())

        # Add insights for each opening that meets the minimum games requirement
        for opening in all_openings:
            if opening.games_played >= min_games:
                opening_insight = OpeningAnalysisInsight(
                    message=f"{opening.name}: {opening.win_rate:.1f}% win rate over {opening.games_played} games",
                    type="opening_stats",
                    opening_name=opening.name,
                    total_games=opening.games_played,
                    win_count=opening.wins,
                    draw_count=opening.draws,
                    loss_count=opening.losses,
                    win_rate=opening.win_rate,
                    avg_game_length=float(total_row.avg_game_length or 0),
                    games_as_white=opening.white_games,
                    games_as_black=opening.black_games,
                    avg_opponent_rating=None,
                    last_played=None,
                    favorite_response=None,
                    variations=[]
                )
                analysis.append(opening_insight.to_dict())
    
    # Find most successful and most played openings
    most_successful_opening = None
    most_played_opening = None
    if all_openings:
        most_successful = max(all_openings, key=lambda x: (x.win_rate, x.games_played))
        most_played = max(all_openings, key=lambda x: x.games_played)
        most_successful_opening = most_successful.name
        most_played_opening = most_played.name
    
    return OpeningAnalysisResponse(
        openings=all_openings,
        analysis=analysis,  # analysis is now a list of dictionaries
        total_openings=total_row.total_openings,
        avg_game_length=float(total_row.avg_game_length or 0),
        total_games=total_row.total_games,
        total_wins=total_row.total_wins,
        total_draws=total_row.total_draws,
        total_losses=total_row.total_losses,
        most_successful=most_successful_opening,
        most_played=most_played_opening
    )

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
        WHERE ({start_date_str}::timestamp IS NULL OR g.date >= {start_date_str}::timestamp)
        AND ({end_date_str}::timestamp IS NULL OR g.date <= {end_date_str}::timestamp)
        GROUP BY o.name
        HAVING COUNT(DISTINCT g.id) >= {min_games}
    )
    SELECT *
    FROM game_stats
    ORDER BY total_games DESC
    """
    
    if limit:
        query += f"\nLIMIT {limit}"
    
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
