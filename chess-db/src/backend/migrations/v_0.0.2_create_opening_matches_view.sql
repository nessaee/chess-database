-- Drop existing view if it exists
DROP MATERIALIZED VIEW IF EXISTS game_opening_matches;

-- Create the optimized materialized view
CREATE MATERIALIZED VIEW game_opening_matches AS
WITH RECURSIVE game_moves AS (
    -- Use partitioned table efficiently
    SELECT 
        id as game_id,
        (get_byte(moves, 0) << 8 | get_byte(moves, 1))::integer as game_move_length,
        substring(moves from 3) as game_moves_no_length,
        id % 8 as partition_num  -- Track partition for analysis
    FROM games
    WHERE moves IS NOT NULL
),
opening_matches AS (
    SELECT DISTINCT ON (g.game_id)
        g.game_id,
        o.id as opening_id,
        g.game_move_length,
        g.partition_num,
        (get_byte(o.moves, 0) << 8 | get_byte(o.moves, 1))::integer as opening_move_length
    FROM game_moves g
    -- Use lateral join for better performance with partitioned data
    CROSS JOIN LATERAL (
        SELECT id, moves, name
        FROM openings o
        WHERE (get_byte(o.moves, 0) << 8 | get_byte(o.moves, 1)) <= g.game_move_length
            AND (get_byte(o.moves, 0) << 8 | get_byte(o.moves, 1)) >= 2
    ) o
    WHERE substring(g.game_moves_no_length for (get_byte(o.moves, 0) << 8 | get_byte(o.moves, 1))) = 
          substring(o.moves from 3 for (get_byte(o.moves, 0) << 8 | get_byte(o.moves, 1)))
    ORDER BY 
        g.game_id,
        (get_byte(o.moves, 0) << 8 | get_byte(o.moves, 1)) DESC,
        array_length(string_to_array(o.name, ':'), 1) DESC
)
SELECT 
    game_id,
    opening_id,
    game_move_length,
    opening_move_length,
    partition_num
FROM opening_matches;

-- Create efficient indexes
CREATE UNIQUE INDEX idx_game_opening_matches_game_id 
ON game_opening_matches (game_id);

CREATE INDEX idx_game_opening_matches_opening 
ON game_opening_matches (opening_id)
INCLUDE (game_move_length, opening_move_length);

-- Add index for partition-based queries
CREATE INDEX idx_game_opening_matches_partition
ON game_opening_matches (partition_num, opening_id)
INCLUDE (game_move_length);

-- Create function to refresh the materialized view
CREATE OR REPLACE FUNCTION refresh_game_opening_matches()
RETURNS void AS $$
BEGIN
    -- Use CONCURRENTLY for zero-downtime refresh
    REFRESH MATERIALIZED VIEW CONCURRENTLY game_opening_matches;
END;
$$ LANGUAGE plpgsql;

-- Create function to refresh specific partition
CREATE OR REPLACE FUNCTION refresh_game_opening_matches_partition(p_num integer)
RETURNS void AS $$
BEGIN
    -- Refresh only games from specified partition
    WITH partition_games AS (
        DELETE FROM game_opening_matches
        WHERE partition_num = p_num
        RETURNING game_id
    ),
    game_moves AS (
        SELECT 
            id as game_id,
            (get_byte(moves, 0) << 8 | get_byte(moves, 1))::integer as game_move_length,
            substring(moves from 3) as game_moves_no_length,
            id % 8 as partition_num
        FROM games
        WHERE id % 8 = p_num
    )
    INSERT INTO game_opening_matches
    SELECT DISTINCT ON (g.game_id)
        g.game_id,
        o.id as opening_id,
        g.game_move_length,
        g.partition_num,
        (get_byte(o.moves, 0) << 8 | get_byte(o.moves, 1))::integer as opening_move_length
    FROM game_moves g
    CROSS JOIN LATERAL (
        SELECT id, moves, name
        FROM openings o
        WHERE (get_byte(o.moves, 0) << 8 | get_byte(o.moves, 1)) <= g.game_move_length
            AND (get_byte(o.moves, 0) << 8 | get_byte(o.moves, 1)) >= 2
    ) o
    WHERE substring(g.game_moves_no_length for (get_byte(o.moves, 0) << 8 | get_byte(o.moves, 1))) = 
          substring(o.moves from 3 for (get_byte(o.moves, 0) << 8 | get_byte(o.moves, 1)))
    ORDER BY 
        g.game_id,
        (get_byte(o.moves, 0) << 8 | get_byte(o.moves, 1)) DESC,
        array_length(string_to_array(o.name, ':'), 1) DESC;
END;
$$ LANGUAGE plpgsql;

-- Analyze the view for query optimization
ANALYZE game_opening_matches;