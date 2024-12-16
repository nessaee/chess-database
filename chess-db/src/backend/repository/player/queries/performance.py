# repository/player/queries/performance.py

"""
SQL queries for player performance analysis.

This module contains complex queries for analyzing player performance,
including rating progression, opening statistics, and head-to-head analysis.
All queries are optimized for performance while maintaining readability.
"""

ANALYZE_PERFORMANCE = """
    WITH player_games AS (
        -- Base game data with calculated fields
        SELECT
            g.*,
            CASE 
                WHEN white_player_id = :player_id THEN 'white'
                ELSE 'black'
            END as player_color,
            CASE
                WHEN white_player_id = :player_id THEN white_elo
                ELSE black_elo
            END as player_rating,
            CASE
                WHEN white_player_id = :player_id THEN black_elo
                ELSE white_elo
            END as opponent_rating,
            CASE
                WHEN (white_player_id = :player_id AND result = '1-0') OR
                     (black_player_id = :player_id AND result = '0-1')
                THEN 'win'
                WHEN result = '1/2-1/2' 
                THEN 'draw'
                ELSE 'loss'
            END as outcome,
            (octet_length(moves) - 19) / 2 as move_count,
            CASE
                WHEN (white_player_id = :player_id AND result = '1-0') OR
                     (black_player_id = :player_id AND result = '0-1')
                THEN 1.0
                WHEN result = '1/2-1/2' THEN 0.5
                ELSE 0.0 
            END as score
        FROM games g
        WHERE (white_player_id = :player_id OR black_player_id = :player_id)
            {% if start_date %}
            AND date >= :start_date::date
            {% endif %}
            {% if end_date %}
            AND date <= :end_date::date
            {% endif %}
    ),
    basic_stats AS (
        -- Overall performance statistics
        SELECT
            COUNT(*) as total_games,
            SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN outcome = 'draw' THEN 1 ELSE 0 END) as draws,
            SUM(CASE WHEN outcome = 'loss' THEN 1 ELSE 0 END) as losses,
            ROUND(AVG(CASE WHEN outcome = 'win' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(move_count), 2) as avg_game_length,
            ROUND(AVG(
                CASE 
                    WHEN player_color = 'white' THEN 1.0 
                    ELSE 0.0 
                END
            ) * 100, 2) as white_percentage,
            ROUND(AVG(score) * 100, 2) as score_percentage
        FROM player_games
    ),
    rating_stats AS (
        -- Rating progression and trends
        SELECT
            MAX(player_rating) as peak_rating,
            FIRST_VALUE(player_rating) OVER (
                ORDER BY date DESC
            ) as current_rating,
            ROUND(AVG(player_rating), 0) as avg_rating,
            -- Calculate rating trend (points per month)
            ROUND(
                REGR_SLOPE(player_rating, 
                    EXTRACT(EPOCH FROM date)::float
                )::numeric * 86400 * 30,  -- Convert to monthly rate
                2
            ) as rating_trend,
            -- Calculate rating volatility
            ROUND(
                STDDEV(player_rating) OVER (
                    ORDER BY date
                    ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                )::numeric,
                2
            ) as rating_volatility
        FROM player_games
        WHERE player_rating IS NOT NULL
    ),
    opening_analysis AS (
        -- Detailed opening statistics
        SELECT
            eco,
            COUNT(*) as games_played,
            SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN outcome = 'loss' THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN outcome = 'draw' THEN 1 ELSE 0 END) as draws,
            ROUND(AVG(CASE WHEN outcome = 'win' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(score) * 100, 2) as score_percentage,
            ROUND(AVG(opponent_rating), 0) as avg_opponent_rating,
            ROUND(
                AVG(opponent_rating + 400 * (2 * score - 1)),
                0
            ) as performance_rating
        FROM player_games
        WHERE eco IS NOT NULL
        GROUP BY eco
        HAVING COUNT(*) >= 3  -- Minimum games threshold
        ORDER BY games_played DESC, win_rate DESC
        LIMIT 10
    ),
    rating_brackets AS (
        -- Performance against different rating ranges
        WITH brackets AS (
            SELECT
                FLOOR(opponent_rating / 100.0) * 100 as bracket_start,
                COUNT(*) as games_played,
                AVG(score) as actual_score,
                AVG(1 / (1 + POWER(10, (opponent_rating - player_rating) / 400.0)))
                    as expected_score
            FROM player_games
            WHERE opponent_rating IS NOT NULL AND player_rating IS NOT NULL
            GROUP BY FLOOR(opponent_rating / 100.0) * 100
            HAVING COUNT(*) >= 3
        )
        SELECT
            bracket_start as min_rating,
            bracket_start + 99 as max_rating,
            games_played,
            ROUND(actual_score * 100, 2) as score_percentage,
            ROUND(
                bracket_start + 400 * LOG(
                    GREATEST(actual_score, 0.001) / 
                    GREATEST(1 - actual_score, 0.001)
                ) / LOG(10),
                0
            ) as performance_rating,
            ROUND(expected_score * 100, 2) as expected_score
        FROM brackets
        ORDER BY bracket_start
    ),
    performance_timeline AS (
        -- Time-based performance analysis
        SELECT
            date_trunc('month', date) as period,
            COUNT(*) as games_played,
            ROUND(AVG(CASE WHEN outcome = 'win' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(opponent_rating), 0) as avg_opponent_rating,
            ROUND(
                AVG(opponent_rating + 400 * (2 * score - 1)),
                0
            ) as performance_rating,
            -- Calculate rating change within period
            FIRST_VALUE(player_rating) OVER (
                PARTITION BY date_trunc('month', date)
                ORDER BY date DESC
            ) -
            FIRST_VALUE(player_rating) OVER (
                PARTITION BY date_trunc('month', date)
                ORDER BY date
            ) as rating_change
        FROM player_games
        WHERE player_rating IS NOT NULL
        GROUP BY date_trunc('month', date)
        ORDER BY period DESC
    )
    -- Combine all analysis components
    SELECT
        (SELECT row_to_json(s.*) FROM basic_stats s) as basic_stats,
        (SELECT row_to_json(r.*) FROM rating_stats r) as rating_stats,
        (SELECT json_agg(o.*) FROM opening_analysis o) as opening_stats,
        (SELECT json_agg(b.*) FROM rating_brackets b) as rating_brackets,
        (SELECT json_agg(t.*) FROM performance_timeline t) as timeline
"""



