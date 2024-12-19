-- Add indexes to improve metrics query performance

-- Create function to manage partition indexes
CREATE OR REPLACE FUNCTION create_partition_indexes(partition_name TEXT)
RETURNS void AS $$
BEGIN
    -- Games table indexes
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS %I ON %I (white_player_id, black_player_id)',
        'idx_' || partition_name || '_players',
        partition_name
    );
    
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS %I ON %I (date) WHERE date IS NOT NULL',
        'idx_' || partition_name || '_date',
        partition_name
    );
    
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS %I ON %I (result)',
        'idx_' || partition_name || '_result',
        partition_name
    );
    
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS %I ON %I (eco) WHERE eco IS NOT NULL',
        'idx_' || partition_name || '_eco',
        partition_name
    );
    
    -- Create combined index for common queries
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS %I ON %I (date DESC, white_player_id, black_player_id) 
        INCLUDE (result, eco, moves) 
        WHERE date IS NOT NULL',
        'idx_' || partition_name || '_combined',
        partition_name
    );
END;
$$ LANGUAGE plpgsql;

-- Create indexes for each games partition
DO $$
DECLARE
    partition_name TEXT;
BEGIN
    FOR partition_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'games_part_%'
    LOOP
        PERFORM create_partition_indexes(partition_name);
    END LOOP;
END $$;

-- Create function to manage endpoint metrics indexes
CREATE OR REPLACE FUNCTION create_endpoint_metrics_indexes(partition_name TEXT)
RETURNS void AS $$
BEGIN
    -- Create combined index for endpoint and method
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS %I ON %I (endpoint, method) 
        INCLUDE (response_time_ms, success)',
        'idx_' || partition_name || '_endpoint_method',
        partition_name
    );
    
    -- Create index for time-based queries
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS %I ON %I (created_at DESC) 
        INCLUDE (response_time_ms, status_code)',
        'idx_' || partition_name || '_created_at',
        partition_name
    );
    
    -- Create index for error analysis
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS %I ON %I (success, status_code) 
        INCLUDE (error_message) 
        WHERE NOT success',
        'idx_' || partition_name || '_errors',
        partition_name
    );
END;
$$ LANGUAGE plpgsql;

-- Create indexes for each endpoint metrics partition
DO $$
DECLARE
    partition_name TEXT;
BEGIN
    FOR partition_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'endpoint_metrics_p%'
    LOOP
        PERFORM create_endpoint_metrics_indexes(partition_name);
    END LOOP;
END $$;

-- Indexes for materialized views
CREATE UNIQUE INDEX IF NOT EXISTS idx_game_opening_matches_pkey 
ON game_opening_matches (game_id, opening_id);

CREATE INDEX IF NOT EXISTS idx_game_opening_matches_opening 
ON game_opening_matches (opening_id)
INCLUDE (game_move_length, opening_move_length);

CREATE INDEX IF NOT EXISTS idx_move_count_stats_moves 
ON move_count_stats (actual_full_moves)
INCLUDE (number_of_games, avg_bytes);

-- Create player_opening_stats table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'player_opening_stats' AND relkind = 'r') THEN
        CREATE TABLE player_opening_stats (
            player_id INTEGER NOT NULL,
            opening_id INTEGER NOT NULL,
            player_name TEXT NOT NULL,
            total_games INTEGER NOT NULL DEFAULT 0,
            wins INTEGER NOT NULL DEFAULT 0,
            draws INTEGER NOT NULL DEFAULT 0,
            losses INTEGER NOT NULL DEFAULT 0,
            win_rate NUMERIC(5,2) NOT NULL DEFAULT 0,
            last_played DATE,
            PRIMARY KEY (player_id, opening_id)
        );
    END IF;
END $$;

-- Create indexes for player_opening_stats
CREATE UNIQUE INDEX IF NOT EXISTS idx_player_opening_stats_pkey 
ON player_opening_stats (player_id, opening_id);

CREATE INDEX IF NOT EXISTS idx_player_opening_stats_metrics 
ON player_opening_stats (total_games DESC, win_rate DESC)
INCLUDE (player_name, last_played)
WHERE total_games >= 10;  -- Only index significant statistics

-- Create function to maintain partition indexes
CREATE OR REPLACE FUNCTION maintain_partition_indexes()
RETURNS void AS $$
DECLARE
    partition_name TEXT;
BEGIN
    -- Handle games partitions
    FOR partition_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'games_part_%'
    LOOP
        PERFORM create_partition_indexes(partition_name);
    END LOOP;
    
    -- Handle endpoint metrics partitions
    FOR partition_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'endpoint_metrics_p%'
    LOOP
        PERFORM create_endpoint_metrics_indexes(partition_name);
    END LOOP;
END;
$$ LANGUAGE plpgsql;
