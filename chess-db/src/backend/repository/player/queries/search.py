# repository/player/queries/search.py

"""SQL queries for player search functionality."""

SEARCH_PLAYERS = """
    WITH player_matches AS (
        -- Find matching players with ranking by match quality
        SELECT 
            p.*,
            CASE 
                WHEN name ILIKE :exact THEN 1       -- Exact match
                WHEN name ILIKE :starts_with THEN 2 -- Prefix match
                WHEN name ILIKE :contains THEN 3    -- Substring match
                ELSE 4                              -- Pattern match
            END as match_rank
        FROM players p
        WHERE name ILIKE :pattern
    )
    {% if include_rating %}
    , recent_ratings AS (
        -- Get most recent rating for each matching player
        SELECT 
            player_id,
            FIRST_VALUE(rating) OVER (
                PARTITION BY player_id 
                ORDER BY game_date DESC
            ) as recent_rating
        FROM (
            SELECT 
                CASE 
                    WHEN white_player_id = pm.id THEN white_player_id
                    ELSE black_player_id 
                END as player_id,
                CASE 
                    WHEN white_player_id = pm.id THEN white_elo
                    ELSE black_elo 
                END as rating,
                date as game_date
            FROM player_matches pm
            JOIN games g ON (
                pm.id = g.white_player_id OR 
                pm.id = g.black_player_id
            )
            WHERE white_elo > 0 OR black_elo > 0
        ) ratings
    )
    {% endif %}
    SELECT 
        pm.id,
        pm.name,
        {% if include_rating %}
        rr.recent_rating as rating,
        {% endif %}
        pm.match_rank
    FROM player_matches pm
    {% if include_rating %}
    LEFT JOIN recent_ratings rr ON pm.id = rr.player_id
    {% endif %}
    ORDER BY 
        pm.match_rank,
        LENGTH(pm.name),
        pm.name
    LIMIT :limit
"""