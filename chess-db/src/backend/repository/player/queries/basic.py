# repository/player/queries/basic.py
"""SQL queries for basic player operations."""

GET_PLAYER = """
    SELECT 
        p.id,
        p.name,
        COUNT(g.id) as total_games,
        MAX(
            CASE 
                WHEN g.white_player_id = p.id THEN g.white_elo
                ELSE g.black_elo
            END
        ) as current_rating
    FROM players p
    LEFT JOIN games g ON (
        p.id = g.white_player_id OR 
        p.id = g.black_player_id
    )
    WHERE p.id = :player_id
    GROUP BY p.id, p.name
"""

LIST_PLAYERS = """
    WITH player_stats AS (
        SELECT
            p.id,
            p.name,
            COUNT(*) as total_games,
            MAX(
                CASE 
                    WHEN white_player_id = p.id THEN white_elo
                    ELSE black_elo
                END
            ) as current_rating,
            MAX(date) as last_active
        FROM players p
        LEFT JOIN games g ON (
            p.id = g.white_player_id OR 
            p.id = g.black_player_id
        )
        GROUP BY p.id, p.name
    )
    SELECT
        ps.*
    FROM player_stats ps
    WHERE 1=1
        {% if min_rating %}
        AND current_rating >= :min_rating
        {% endif %}
        {% if max_rating %}
        AND current_rating <= :max_rating
        {% endif %}
        {% if active_since %}
        AND last_active >= :active_since::date
        {% endif %}
        {% if min_games %}
        AND total_games >= :min_games
        {% endif %}
    ORDER BY
        {% if order_by == 'rating' %}
        current_rating DESC NULLS LAST
        {% elif order_by == 'games_played' %}
        total_games DESC
        {% else %}
        name ASC
        {% endif %}
    {% if limit %}
    LIMIT :limit
    {% endif %}
    {% if offset %}
    OFFSET :offset
    {% endif %}
"""

DELETE_PLAYER = """
    WITH deleted_games AS (
        DELETE FROM games
        WHERE white_player_id = :player_id
           OR black_player_id = :player_id
    )
    DELETE FROM players
    WHERE id = :player_id
    RETURNING id
"""