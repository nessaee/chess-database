-- Create materialized view for move count statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS move_count_stats AS
WITH game_moves_analysis AS (
    SELECT
        -- Extract move count from first two bytes
        get_byte(moves, 0) << 8 | get_byte(moves, 1) as stored_move_count,
        -- Calculate actual moves from remaining binary data length
        (octet_length(moves) - 2) / 2 as actual_full_moves,
        -- Game metadata
        octet_length(moves) as total_bytes,
        -- Add partition info for analysis
        id % 8 as partition_num
    FROM games
    WHERE moves IS NOT NULL
        AND octet_length(moves) >= 2  -- Ensure minimum size for move count
),
partition_counts AS (
    SELECT 
        actual_full_moves,
        partition_num,
        COUNT(*) as partition_count
    FROM game_moves_analysis
    GROUP BY actual_full_moves, partition_num
)
SELECT
    gma.actual_full_moves,
    COUNT(*) as number_of_games,
    ROUND(AVG(gma.total_bytes)::numeric, 2) as avg_bytes,
    -- Add partition distribution stats
    jsonb_object_agg(
        COALESCE(pc.partition_num::text, '0'), 
        COALESCE(pc.partition_count, 0)
    ) as partition_distribution,
    -- Add timestamp for tracking last update
    CURRENT_TIMESTAMP as last_updated
FROM game_moves_analysis gma
LEFT JOIN partition_counts pc 
    ON gma.actual_full_moves = pc.actual_full_moves 
    AND gma.partition_num = pc.partition_num
WHERE 
    gma.actual_full_moves >= 0
    AND gma.actual_full_moves <= 500  -- Reasonable maximum game length
    AND gma.stored_move_count >= 0    -- Ensure valid move count
    AND gma.stored_move_count <= 500  -- Reasonable maximum stored moves
GROUP BY gma.actual_full_moves
ORDER BY gma.actual_full_moves ASC;

-- Create index on the most frequently queried column
CREATE INDEX IF NOT EXISTS idx_move_count_stats_moves 
ON move_count_stats(actual_full_moves);

-- Create function to refresh the materialized view
CREATE OR REPLACE FUNCTION refresh_move_count_stats()
RETURNS void AS $$
BEGIN
    -- Use CONCURRENTLY for zero-downtime refresh
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

-- Drop old trigger if exists
DROP TRIGGER IF EXISTS games_move_count_stats_refresh ON games;

-- Create new trigger on the partitioned table
CREATE TRIGGER games_move_count_stats_refresh
AFTER INSERT OR UPDATE OR DELETE ON games
FOR EACH STATEMENT
EXECUTE FUNCTION trigger_refresh_move_count_stats();
