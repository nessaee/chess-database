-- Migration: Optimize storage for games table
-- Version: 002

-- Create migrations table if it doesn't exist
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Check if already applied
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = '002_optimize_storage') THEN
        RAISE NOTICE 'Migration already applied';
        RETURN;
    END IF;
END $$;

-- First, let's check our date ranges
DO $$
DECLARE
    min_date date;
    max_date date;
    null_count integer;
BEGIN
    SELECT MIN(date), MAX(date), COUNT(*) FILTER (WHERE date IS NULL)
    INTO min_date, max_date, null_count
    FROM games;
    
    RAISE NOTICE 'Date range: % to %', min_date, max_date;
    RAISE NOTICE 'Games with NULL dates: %', null_count;
END $$;

-- 1. Create new partitioned table
DROP TABLE IF EXISTS games_new CASCADE;
CREATE TABLE games_new (
    id integer NOT NULL,
    white_player_id integer,
    black_player_id integer,
    white_elo smallint,  -- Changed from integer
    black_elo smallint,  -- Changed from integer
    date date,          -- Allow NULL dates
    eco char(3),        -- Changed from varchar(10)
    moves bytea,
    result smallint,
    CONSTRAINT games_new_pkey PRIMARY KEY (id),
    CONSTRAINT games_new_white_player_id_fkey FOREIGN KEY (white_player_id) REFERENCES players(id),
    CONSTRAINT games_new_black_player_id_fkey FOREIGN KEY (black_player_id) REFERENCES players(id),
    CONSTRAINT result_check CHECK (result >= 0 AND result <= 3)
) PARTITION BY HASH (id);

-- Create 8 hash partitions for even distribution
CREATE TABLE games_part_0 PARTITION OF games_new FOR VALUES WITH (MODULUS 8, REMAINDER 0);
CREATE TABLE games_part_1 PARTITION OF games_new FOR VALUES WITH (MODULUS 8, REMAINDER 1);
CREATE TABLE games_part_2 PARTITION OF games_new FOR VALUES WITH (MODULUS 8, REMAINDER 2);
CREATE TABLE games_part_3 PARTITION OF games_new FOR VALUES WITH (MODULUS 8, REMAINDER 3);
CREATE TABLE games_part_4 PARTITION OF games_new FOR VALUES WITH (MODULUS 8, REMAINDER 4);
CREATE TABLE games_part_5 PARTITION OF games_new FOR VALUES WITH (MODULUS 8, REMAINDER 5);
CREATE TABLE games_part_6 PARTITION OF games_new FOR VALUES WITH (MODULUS 8, REMAINDER 6);
CREATE TABLE games_part_7 PARTITION OF games_new FOR VALUES WITH (MODULUS 8, REMAINDER 7);

-- Create a function to process a batch
CREATE OR REPLACE FUNCTION process_games_batch(
    start_id INTEGER,
    batch_size INTEGER
) RETURNS TABLE (
    processed INTEGER,
    max_id INTEGER
) AS $$
DECLARE
    batch_count INTEGER;
    max_processed_id INTEGER;
BEGIN
    WITH to_move AS (
        SELECT id, white_player_id, black_player_id, 
               CASE WHEN white_elo > 32767 THEN 32767 
                    WHEN white_elo < -32768 THEN -32768 
                    ELSE white_elo::smallint END as white_elo,
               CASE WHEN black_elo > 32767 THEN 32767 
                    WHEN black_elo < -32768 THEN -32768 
                    ELSE black_elo::smallint END as black_elo,
               date, 
               CASE WHEN eco IS NULL THEN NULL 
                    ELSE substring(eco from 1 for 3) END as eco,
               moves, result
        FROM games
        WHERE id > start_id
        ORDER BY id
        LIMIT batch_size
        FOR UPDATE SKIP LOCKED
    )
    INSERT INTO games_new 
    SELECT * FROM to_move;
    
    GET DIAGNOSTICS batch_count = ROW_COUNT;
    
    IF batch_count > 0 THEN
        SELECT MAX(id) INTO max_processed_id FROM games_new WHERE id > start_id;
    ELSE
        max_processed_id := start_id;
    END IF;
    
    RETURN QUERY SELECT batch_count, max_processed_id;
END;
$$ LANGUAGE plpgsql;

-- Process batches
DO $$
DECLARE
    batch_size INTEGER := 50000;
    total_rows INTEGER;
    total_processed INTEGER := 0;
    current_id INTEGER := 0;
    batch_result RECORD;
    start_ts TIMESTAMP;
    last_progress_ts TIMESTAMP;
    current_ts TIMESTAMP;
BEGIN
    SELECT COUNT(*) INTO total_rows FROM games;
    start_ts := clock_timestamp();
    last_progress_ts := start_ts;
    
    RAISE NOTICE 'Starting migration of % rows at %', total_rows, start_ts;

    LOOP
        SELECT * INTO batch_result 
        FROM process_games_batch(current_id, batch_size);
        
        IF batch_result.processed = 0 THEN
            EXIT;
        END IF;
        
        total_processed := total_processed + batch_result.processed;
        current_id := batch_result.max_id;
        
        current_ts := clock_timestamp();
        IF current_ts - last_progress_ts >= interval '10 seconds' THEN
            RAISE NOTICE 'Processed % of % rows (%.2f%%) in %', 
                total_processed, total_rows, 
                (total_processed::float / total_rows::float * 100.0),
                age(current_ts, start_ts);
            last_progress_ts := current_ts;
        END IF;
    END LOOP;
    
    current_ts := clock_timestamp();
    RAISE NOTICE 'Migration completed: % rows processed in %', 
        total_processed, 
        age(current_ts, start_ts);
END $$;

-- Drop the batch processing function
DROP FUNCTION IF EXISTS process_games_batch(INTEGER, INTEGER);

-- 4. Verify data
DO $$
DECLARE
    old_count INTEGER;
    new_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO old_count FROM games;
    SELECT COUNT(*) INTO new_count FROM games_new;
    
    IF old_count != new_count THEN
        RAISE EXCEPTION 'Data verification failed. Old count: %, New count: %', old_count, new_count;
    END IF;
    
    RAISE NOTICE 'Data verification passed. Both tables have % rows', old_count;
END $$;

-- 5. Create optimized indexes
CREATE INDEX idx_games_new_date ON games_new(date) WHERE date IS NOT NULL;
CREATE INDEX idx_games_new_eco ON games_new(eco) WHERE eco IS NOT NULL;
CREATE INDEX idx_games_new_players ON games_new(white_player_id, black_player_id);

-- Create partial indexes for common ELO ranges
CREATE INDEX idx_games_new_high_rated ON games_new(white_elo, black_elo)
    WHERE white_elo >= 2200 OR black_elo >= 2200;

-- 6. Swap tables
ALTER TABLE games RENAME TO games_old;
ALTER TABLE games_new RENAME TO games;
ALTER TABLE games_old SET (autovacuum_enabled = false);

-- 7. Drop old table (consider keeping it for a while in production)
-- DROP TABLE games_old;

-- Record migration
INSERT INTO schema_migrations (version) VALUES ('002_optimize_storage');
