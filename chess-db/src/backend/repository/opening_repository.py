"""
Repository functions for opening analysis.
"""

from typing import List, Optional, Tuple
from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .models.opening import OpeningStats, OpeningAnalysisResponse, PopularOpeningStats, AnalysisInsight, OpeningVariationStats

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
        SELECT *
        FROM game_opening_matches
        WHERE (white_player_id::text = '{username}' OR black_player_id::text = '{username}')
        AND ({start_date_str}::timestamp IS NULL OR date >= {start_date_str}::timestamp)
        AND ({end_date_str}::timestamp IS NULL OR date <= {end_date_str}::timestamp)
    ),
    opening_totals AS (
        SELECT 
            COUNT(pg.game_id) as total_games,
            SUM(CASE WHEN pg.result = '1-0' AND '{username}' = pg.white_player_id::text OR 
                     pg.result = '0-1' AND '{username}' = pg.black_player_id::text THEN 1 ELSE 0 END) as total_wins,
            SUM(CASE WHEN pg.result = '1/2-1/2' THEN 1 ELSE 0 END) as total_draws,
            SUM(CASE WHEN pg.result = '1-0' AND '{username}' = pg.black_player_id::text OR 
                     pg.result = '0-1' AND '{username}' = pg.white_player_id::text THEN 1 ELSE 0 END) as total_losses,
            COUNT(DISTINCT pg.opening_name) as total_openings,
            AVG(pg.move_length) as avg_game_length
        FROM player_games pg
    )
    SELECT * FROM opening_totals
    """
    
    # Log the total query for debugging
    print(f"Executing total query:\n{total_query}")
    
    total_result = await db.execute(text(total_query))
    total_row = total_result.fetchone()
    
    # Log the total stats for debugging
    print(f"Total stats: Games: {total_row.total_games}, Openings: {total_row.total_openings}, Win Rate: {(total_row.total_wins / total_row.total_games * 100):.2f}%")
    
    # Get all openings without limit for analysis
    all_openings_query = f"""
    WITH player_games AS (
        SELECT *
        FROM game_opening_matches gom
        WHERE (white_player_id::text = '{username}' OR black_player_id::text = '{username}')
        AND ({start_date_str}::timestamp IS NULL OR date >= {start_date_str}::timestamp)
        AND ({end_date_str}::timestamp IS NULL OR date <= {end_date_str}::timestamp)
    ),
    most_specific_openings AS (
        SELECT DISTINCT ON (game_id)
            game_id,
            opening_name,
            white_player_id,
            black_player_id,
            result,
            date,
            LENGTH(opening_name) as name_length
        FROM player_games
        ORDER BY game_id, LENGTH(opening_name) DESC
    )
    SELECT 
        mso.opening_name as name,
        COUNT(*) as games_played,
        SUM(CASE WHEN mso.result = '1-0' AND '{username}' = mso.white_player_id::text OR 
                 mso.result = '0-1' AND '{username}' = mso.black_player_id::text THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN mso.result = '1/2-1/2' THEN 1 ELSE 0 END) as draws,
        SUM(CASE WHEN mso.result = '1-0' AND '{username}' = mso.black_player_id::text OR 
                 mso.result = '0-1' AND '{username}' = mso.white_player_id::text THEN 1 ELSE 0 END) as losses,
        SUM(CASE WHEN '{username}' = mso.white_player_id::text THEN 1 ELSE 0 END) as white_games,
        SUM(CASE WHEN '{username}' = mso.black_player_id::text THEN 1 ELSE 0 END) as black_games,
        ROUND((SUM(CASE WHEN mso.result = '1-0' AND '{username}' = mso.white_player_id::text OR 
                 mso.result = '0-1' AND '{username}' = mso.black_player_id::text THEN 1 ELSE 0 END)::float / COUNT(*) * 100)::numeric, 2) as win_rate,
        ROUND((SUM(CASE WHEN mso.result = '1/2-1/2' THEN 1 ELSE 0 END)::float / COUNT(*) * 100)::numeric, 2) as draw_rate
    FROM most_specific_openings mso
    GROUP BY mso.opening_name
    HAVING COUNT(*) >= {min_games}
    ORDER BY COUNT(*) DESC
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
            wins=row.wins,
            draws=row.draws,
            losses=row.losses,
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
        
        analysis.append(AnalysisInsight(
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
        ))

        # Best opening insight
        if all_openings:
            best_opening = max(all_openings, key=lambda x: (x.win_rate, x.games_played))
            analysis.append(AnalysisInsight(
                message=f"Best opening: {best_opening.name} with {best_opening.win_rate}% win rate over {best_opening.games_played} games",
                type="best_opening",
                opening_name=best_opening.name,
                total_games=best_opening.games_played,
                win_count=best_opening.wins,
                draw_count=best_opening.draws,
                loss_count=best_opening.losses,
                win_rate=best_opening.win_rate,
                avg_game_length=float(total_row.avg_game_length or 0),
                games_as_white=best_opening.white_games,
                games_as_black=best_opening.black_games,
                avg_opponent_rating=None,
                last_played=None,
                favorite_response=None,
                variations=[]
            ))
    
    # Find most successful and most played openings
    most_successful_opening = None
    most_played_opening = None
    if all_openings:
        most_successful = max(all_openings, key=lambda x: (x.win_rate, x.games_played))
        most_played = max(all_openings, key=lambda x: x.games_played)
        most_successful_opening = most_successful.name
        most_played_opening = most_played.name
        
        # Sort openings by frequency (games_played)
        all_openings.sort(key=lambda x: x.games_played, reverse=True)
    
    return OpeningAnalysisResponse(
        openings=all_openings,  # Return sorted openings
        analysis=analysis,
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
    limit: int = 10
) -> List[PopularOpeningStats]:
    """Get statistics for popular openings."""
    
    query = """
    WITH opening_stats AS (
        SELECT 
            gom.opening_name as name,
            COUNT(*) as total_games,
            AVG(CASE 
                WHEN gom.result = '1-0' THEN 1
                WHEN gom.result = '0-1' THEN 0
                ELSE 0.5
            END) * 100 as white_win_rate,
            COUNT(DISTINCT CASE WHEN gom.white_player_id = player_id THEN gom.white_player_id
                              WHEN gom.black_player_id = player_id THEN gom.black_player_id
                         END) as unique_players
        FROM game_opening_matches gom
        WHERE (:start_date::timestamp IS NULL OR gom.date >= :start_date::timestamp)
        AND (:end_date::timestamp IS NULL OR gom.date <= :end_date::timestamp)
        GROUP BY gom.opening_name
        HAVING COUNT(*) >= :min_games::integer
        ORDER BY total_games DESC
        LIMIT :limit::integer
    ),
    opening_variants AS (
        SELECT 
            os.name,
            gom.opening_name as variant_name,
            COUNT(*) as variant_games,
            AVG(CASE 
                WHEN gom.result = '1-0' THEN 1
                WHEN gom.result = '0-1' THEN 0
                ELSE 0.5
            END) * 100 as variant_win_rate
        FROM game_opening_matches gom
        JOIN opening_stats os ON os.name = gom.opening_name
        WHERE (:start_date::timestamp IS NULL OR gom.date >= :start_date::timestamp)
        AND (:end_date::timestamp IS NULL OR gom.date <= :end_date::timestamp)
        GROUP BY os.name, gom.opening_name
    )
    SELECT 
        os.*,
        COALESCE(json_agg(
            json_build_object(
                'name', ov.variant_name,
                'total_games', ov.variant_games,
                'points', ov.variant_games * (ov.variant_win_rate / 100),
                'win_rate', ov.variant_win_rate
            )
        ) FILTER (WHERE ov.variant_name IS NOT NULL), '[]') as variants
    FROM opening_stats os
    LEFT JOIN opening_variants ov ON os.name = ov.name
    GROUP BY os.name, os.total_games, os.white_win_rate, os.unique_players
    ORDER BY os.total_games DESC
    """
    
    result = await db.execute(
        text(query),
        {
            "start_date": start_date,
            "end_date": end_date,
            "min_games": min_games,
            "limit": limit
        }
    )
    
    return [
        PopularOpeningStats(
            name=row.name,
            total_games=row.total_games,
            white_win_rate=row.white_win_rate,
            unique_players=row.unique_players,
            variants=row.variants
        )
        for row in result.fetchall()
    ]
