# player/queries/analysis.py
"""Queries for analyzing player performance and statistics."""

GET_PLAYER_ANALYSIS = """
    WITH player_games AS (
        -- Base game statistics with calculated fields
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
                WHEN (white_player_id = :player_id AND result = '1-0') OR
                     (black_player_id = :player_id AND result = '0-1')
                THEN 'win'
                WHEN result = '1/2-1/2' 
                THEN 'draw'
                ELSE 'loss'
            END as outcome,
            (octet_length(moves) - 19) / 2 as move_count
        FROM games g
        WHERE (white_player_id = :player_id OR black_player_id = :player_id)
            {% if start_date %}
            AND date >= :start_date::date
            {% endif %}
            {% if end_date %}
            AND date <= :end_date::date
            {% endif %}
    ),
    overview_stats AS (
        -- Calculate overall performance metrics
        SELECT
            COUNT(*) as total_games,
            SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN outcome = 'draw' THEN 1 ELSE 0 END) as draws,
            SUM(CASE WHEN outcome = 'loss' THEN 1 ELSE 0 END) as losses,
            ROUND(AVG(CASE WHEN outcome = 'win' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
            ROUND(AVG(move_count), 2) as avg_game_length,
            SUM(CASE WHEN player_color = 'white' THEN 1 ELSE 0 END) as white_games,
            SUM(CASE WHEN player_color = 'black' THEN 1 ELSE 0 END) as black_games
    ),
    rating_progression AS (
        -- Analyze rating progression over time
        SELECT
            MIN(player_rating) as min_rating,
            MAX(player_rating) as peak_rating,
            ROUND(AVG(player_rating), 0) as avg_rating,
            FIRST_VALUE(player_rating) OVER (ORDER BY date DESC) as current_rating,
            ROUND(
                STDDEV(player_rating) OVER (
                    ORDER BY date
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                ),
                2
            ) as rating_volatility
        FROM player_games
        WHERE player_rating IS NOT NULL
    ),
    opening_analysis AS (
        -- Analyze performance with different openings
        SELECT
            eco,
            COUNT(*) as games_played,
            SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN outcome = 'draw' THEN 1 ELSE 0 END) as draws,
            ROUND(
                AVG(CASE 
                    WHEN outcome = 'win' THEN 1.0 
                    WHEN outcome = 'draw' THEN 0.5
                    ELSE 0.0 
                END) * 100,
                2
            ) as score_percentage,
            AVG(move_count) as avg_length
        FROM player_games
        WHERE eco IS NOT NULL
        GROUP BY eco
        HAVING COUNT(*) >= :min_opening_games
        ORDER BY count(*) DESC
    ),
    time_performance AS (
        -- Analyze performance over time periods
        SELECT
            date_trunc(:time_group, date) as period,
            COUNT(*) as games_played,
            SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as wins,
            ROUND(
                AVG(CASE WHEN outcome = 'win' THEN 1.0 ELSE 0.0 END) * 100,
                2
            ) as win_rate,
            ROUND(AVG(player_rating), 0) as avg_rating,
            ROUND(AVG(move_count), 2) as avg_moves
        FROM player_games
        GROUP BY date_trunc(:time_group, date)
        ORDER BY period DESC
    )
    SELECT
        json_build_object(
            'overview', (SELECT row_to_json(o.*) FROM overview_stats o),
            'ratings', (SELECT row_to_json(r.*) FROM rating_progression r),
            'openings', (SELECT json_agg(o.*) FROM opening_analysis o),
            'timeline', (SELECT json_agg(t.*) FROM time_performance t)
        ) as analysis
"""

GET_PLAYING_STYLE = """
    WITH style_metrics AS (
        SELECT
            -- Game length preferences
            AVG(move_count) as avg_game_length,
            STDDEV(move_count) as game_length_variance,
            
            -- Opening preferences
            mode() WITHIN GROUP (ORDER BY eco) as favorite_opening,
            COUNT(DISTINCT eco) as opening_diversity,
            
            -- Color performance
            ROUND(
                AVG(CASE 
                    WHEN player_color = 'white' AND outcome = 'win' THEN 1.0
                    WHEN player_color = 'white' AND outcome = 'draw' THEN 0.5
                    ELSE 0.0 
                END) * 100,
                2
            ) as white_score_percentage,
            
            ROUND(
                AVG(CASE 
                    WHEN player_color = 'black' AND outcome = 'win' THEN 1.0
                    WHEN player_color = 'black' AND outcome = 'draw' THEN 0.5
                    ELSE 0.0 
                END) * 100,
                2
            ) as black_score_percentage,
            
            -- Decisiveness
            ROUND(
                (COUNT(*) FILTER (WHERE outcome != 'draw')::float / 
                NULLIF(COUNT(*), 0) * 100),
                2
            ) as decisive_game_percentage
            
        FROM player_games
    ),
    position_stats AS (
        -- Analyze typical positions and piece placement
        SELECT
            COUNT(*) as total_positions,
            mode() WITHIN GROUP (ORDER BY piece_placement) as common_structure,
            AVG(material_balance) as avg_material_balance
        FROM (
            SELECT 
                regexp_split_to_table(position_sequence, ',') as piece_placement,
                material_count as material_balance
            FROM game_positions gp
            WHERE gp.game_id IN (SELECT id FROM player_games)
        ) positions
    )
    SELECT
        json_build_object(
            'game_length', json_build_object(
                'average', avg_game_length,
                'variance', game_length_variance
            ),
            'opening_choices', json_build_object(
                'favorite', favorite_opening,
                'diversity_index', opening_diversity
            ),
            'color_performance', json_build_object(
                'white_score', white_score_percentage,
                'black_score', black_score_percentage
            ),
            'playing_characteristics', json_build_object(
                'decisiveness', decisive_game_percentage,
                'typical_structure', common_structure,
                'material_balance', avg_material_balance
            )
        ) as style_analysis
    FROM style_metrics, position_stats
"""

GET_OPPONENT_STRENGTH = """
    WITH opponent_levels AS (
        SELECT
            CASE
                WHEN opponent_rating >= 2500 THEN 'grandmaster'
                WHEN opponent_rating >= 2400 THEN 'international_master'
                WHEN opponent_rating >= 2200 THEN 'master'
                WHEN opponent_rating >= 2000 THEN 'expert'
                ELSE 'other'
            END as strength_category,
            COUNT(*) as games_played,
            ROUND(
                AVG(CASE 
                    WHEN outcome = 'win' THEN 1.0
                    WHEN outcome = 'draw' THEN 0.5
                    ELSE 0.0
                END) * 100,
                2
            ) as score_percentage,
            ROUND(AVG(opponent_rating), 0) as avg_opponent_rating
        FROM (
            SELECT
                g.*,
                CASE
                    WHEN white_player_id = :player_id THEN black_elo
                    ELSE white_elo
                END as opponent_rating,
                CASE
                    WHEN (white_player_id = :player_id AND result = '1-0') OR
                         (black_player_id = :player_id AND result = '0-1')
                    THEN 'win'
                    WHEN result = '1/2-1/2' THEN 'draw'
                    ELSE 'loss'
                END as outcome
            FROM games g
            WHERE (white_player_id = :player_id OR black_player_id = :player_id)
                AND (white_elo IS NOT NULL AND black_elo IS NOT NULL)
                {% if start_date %}
                AND date >= :start_date::date
                {% endif %}
                {% if end_date %}
                AND date <= :end_date::date
                {% endif %}
        ) rated_games
        GROUP BY strength_category
    )
    SELECT
        json_build_object(
            'strength_levels', (
                SELECT json_agg(
                    json_build_object(
                        'category', strength_category,
                        'games', games_played,
                        'score', score_percentage,
                        'avg_rating', avg_opponent_rating
                    )
                )
                FROM opponent_levels
            ),
            'rating_ranges', (
                SELECT json_agg(
                    json_build_object(
                        'range_start', floor(opponent_rating/100)*100,
                        'range_end', floor(opponent_rating/100)*100 + 99,
                        'games', COUNT(*),
                        'score', ROUND(AVG(CASE 
                            WHEN outcome = 'win' THEN 1.0
                            WHEN outcome = 'draw' THEN 0.5
                            ELSE 0.0
                        END) * 100, 2)
                    )
                )
                FROM rated_games
                GROUP BY floor(opponent_rating/100)
                ORDER BY floor(opponent_rating/100)
            )
        ) as opponent_analysis
"""