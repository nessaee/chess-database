# repository/game/queries.py
# Base game retrieval query
GET_GAMES_QUERY = """
    SELECT
        g.id,
        g.white_player_id,
        g.black_player_id,
        p1.name as white_player_name,
        p2.name as black_player_name,
        g.date,
        g.result,
        g.eco,
        g.moves,
        g.white_elo,
        g.black_elo
    FROM games g
    JOIN players p1 ON g.white_player_id = p1.id
    JOIN players p2 ON g.black_player_id = p2.id
    ORDER BY g.date DESC
    LIMIT :limit
    OFFSET :offset
"""

# Single game query
GET_GAME_QUERY = """
    SELECT
        g.id,
        g.white_player_id,
        g.black_player_id,
        p1.name as white_player_name,
        p2.name as black_player_name,
        g.date,
        g.result,
        g.eco,
        g.moves,
        g.white_elo,
        g.black_elo
    FROM games g
    JOIN players p1 ON g.white_player_id = p1.id
    JOIN players p2 ON g.black_player_id = p2.id
    WHERE g.id = :game_id
"""

# Game creation query
CREATE_GAME_QUERY = """
    INSERT INTO games (
        white_player_id,
        black_player_id,
        date,
        result,
        eco,
        moves,
        white_elo,
        black_elo
    ) VALUES (
        :white_player_id,
        :black_player_id,
        :date,
        :result,
        :eco,
        :moves,
        :white_elo,
        :black_elo
    )
    RETURNING id
"""

# Game statistics query
GET_GAME_STATS_QUERY = """
    WITH game_stats AS (
        SELECT
            COUNT(*) as total_games,
            COUNT(DISTINCT white_player_id) + 
            COUNT(DISTINCT black_player_id) as total_players,
            AVG((octet_length(moves) - 19) / 2) as avg_game_length,
            MIN(date) as earliest_date,
            MAX(date) as latest_date
        FROM games
        WHERE date IS NOT NULL
            {% if start_date %}
            AND date >= :start_date::date
            {% endif %}
            {% if end_date %}
            AND date <= :end_date::date
            {% endif %}
    ),
    eco_dist AS (
        SELECT
            eco,
            COUNT(*) as count
        FROM games
        WHERE eco IS NOT NULL
        GROUP BY eco
        ORDER BY count DESC
    ),
    rating_dist AS (
        SELECT
            floor(rating/100)*100 as rating_bracket,
            COUNT(*) as count
        FROM (
            SELECT white_elo as rating FROM games WHERE white_elo IS NOT NULL
            UNION ALL
            SELECT black_elo FROM games WHERE black_elo IS NOT NULL
        ) ratings
        GROUP BY floor(rating/100)
        ORDER BY rating_bracket
    ),
    result_dist AS (
        SELECT
            result,
            COUNT(*) as count
        FROM games
        GROUP BY result
    )
    SELECT
        s.total_games,
        s.total_players,
        s.avg_game_length,
        json_object_agg(e.eco, e.count) as eco_distribution,
        json_object_agg(
            r.rating_bracket::text, 
            r.count
        ) as rating_distribution,
        json_object_agg(rd.result, rd.count) as result_distribution,
        s.earliest_date,
        s.latest_date
    FROM game_stats s
    CROSS JOIN LATERAL (
        SELECT * FROM eco_dist
    ) e
    CROSS JOIN LATERAL (
        SELECT * FROM rating_dist
    ) r
    CROSS JOIN LATERAL (
        SELECT * FROM result_dist
    ) rd
    GROUP BY
        s.total_games,
        s.total_players,
        s.avg_game_length,
        s.earliest_date,
        s.latest_date
"""