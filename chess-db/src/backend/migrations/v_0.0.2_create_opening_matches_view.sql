-- Drop existing view if it exists
DROP MATERIALIZED VIEW IF EXISTS game_opening_matches;

-- Create the optimized materialized view
CREATE MATERIALIZED VIEW game_opening_matches AS
WITH game_moves AS (
    SELECT 
        id as game_id,
        (get_byte(moves::bytea, 0) << 8 | get_byte(moves::bytea, 1))::integer as game_move_length,
        substring(moves::bytea from 3) as game_moves_no_length
    FROM games
),
opening_matches AS (
    SELECT DISTINCT ON (g.game_id)
        g.game_id,
        o.id as opening_id,
        g.game_move_length,
        (get_byte(o.moves::bytea, 0) << 8 | get_byte(o.moves::bytea, 1))::integer as opening_move_length
    FROM game_moves g
    CROSS JOIN openings o
    WHERE (get_byte(o.moves::bytea, 0) << 8 | get_byte(o.moves::bytea, 1)) <= g.game_move_length
        AND (get_byte(o.moves::bytea, 0) << 8 | get_byte(o.moves::bytea, 1)) >= 2
        AND substring(g.game_moves_no_length for (get_byte(o.moves::bytea, 0) << 8 | get_byte(o.moves::bytea, 1))) = 
            substring(o.moves::bytea from 3 for (get_byte(o.moves::bytea, 0) << 8 | get_byte(o.moves::bytea, 1)))
    ORDER BY 
        g.game_id,
        (get_byte(o.moves::bytea, 0) << 8 | get_byte(o.moves::bytea, 1)) DESC,
        array_length(string_to_array(o.name, ':'), 1) DESC
)
SELECT * FROM opening_matches;

-- Create efficient indexes
CREATE UNIQUE INDEX idx_game_opening_matches_game_id 
ON game_opening_matches (game_id);

CREATE INDEX idx_game_opening_matches_opening 
ON game_opening_matches (opening_id)
INCLUDE (game_move_length, opening_move_length);

-- Create function to refresh the materialized view
CREATE OR REPLACE FUNCTION refresh_game_opening_matches()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY game_opening_matches;
END;
$$ LANGUAGE plpgsql;

-- Analyze the view for query optimization
ANALYZE game_opening_matches;