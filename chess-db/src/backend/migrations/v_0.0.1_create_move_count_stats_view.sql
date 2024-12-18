-- Create materialized view for move count statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS move_count_stats AS
WITH game_moves_analysis AS (
    SELECT
        -- Extract move count from first two bytes
        get_byte(moves, 0) << 8 | get_byte(moves, 1) as stored_move_count,
        -- Calculate actual moves from remaining binary data length
        (octet_length(moves) - 2) / 2 as actual_full_moves,
        -- Game metadata
        octet_length(moves) as total_bytes
    FROM games
    WHERE moves IS NOT NULL
        AND octet_length(moves) >= 2  -- Ensure minimum size for move count
)
SELECT
    actual_full_moves,
    COUNT(*) as number_of_games,
    ROUND(AVG(total_bytes)::numeric, 2) as avg_bytes,
    -- Add timestamp for tracking last update
    CURRENT_TIMESTAMP as last_updated
FROM game_moves_analysis
WHERE 
    actual_full_moves >= 0
    AND actual_full_moves <= 500  -- Reasonable maximum game length
    AND stored_move_count >= 0    -- Ensure valid move count
    AND stored_move_count <= 500  -- Reasonable maximum stored moves
GROUP BY actual_full_moves
ORDER BY actual_full_moves ASC;

-- Create index on the most frequently queried column
CREATE INDEX IF NOT EXISTS idx_move_count_stats_moves 
ON move_count_stats(actual_full_moves);

-- Create function to refresh the materialized view
CREATE OR REPLACE FUNCTION refresh_move_count_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY move_count_stats;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to refresh the view when games table changes
CREATE OR REPLACE FUNCTION trigger_refresh_move_count_stats()
RETURNS trigger AS $$
BEGIN
    -- Refresh the materialized view asynchronously
    PERFORM pg_notify('refresh_move_count_stats', '');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER games_move_count_stats_refresh
AFTER INSERT OR UPDATE OR DELETE ON games
FOR EACH STATEMENT
EXECUTE FUNCTION trigger_refresh_move_count_stats();
