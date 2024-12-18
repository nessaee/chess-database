-- Migration: Convert game results to 2-bit representation
-- Version: 001

-- First increase WAL size
ALTER SYSTEM SET max_wal_size = '4GB';
SELECT pg_reload_conf();

-- Create migrations table if it doesn't exist
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Check if already applied and completed
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'games' 
        AND column_name = 'result' 
        AND data_type = 'smallint'
    ) THEN
        IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = '001_convert_result_to_bits') THEN
            RAISE NOTICE 'Migration already completed successfully';
            RETURN;
        ELSE
            -- Migration completed but not recorded
            INSERT INTO schema_migrations (version) VALUES ('001_convert_result_to_bits');
            RAISE NOTICE 'Migration was completed but not recorded. Recording now.';
            RETURN;
        END IF;
    END IF;
END $$;

-- Add new column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'games' 
        AND column_name = 'result_bits'
    ) THEN
        ALTER TABLE games ADD COLUMN result_bits SMALLINT;
    END IF;
END $$;

-- Create a function to process batches
CREATE OR REPLACE FUNCTION process_result_batch(batch_size INTEGER) RETURNS INTEGER AS $$
DECLARE
    rows_updated INTEGER;
BEGIN
    WITH to_update AS (
        SELECT id 
        FROM games 
        WHERE result_bits IS NULL 
        LIMIT batch_size
        FOR UPDATE SKIP LOCKED
    )
    UPDATE games g
    SET result_bits = CASE g.result
        WHEN '1/2-1/2' THEN 1
        WHEN '1-0' THEN 2
        WHEN '0-1' THEN 3
        ELSE 0
    END
    FROM to_update
    WHERE g.id = to_update.id;
    
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    RETURN rows_updated;
END;
$$ LANGUAGE plpgsql;

-- Process batches
BEGIN;
DO $$
DECLARE
    batch_size INTEGER := 100000;
    total_processed INTEGER := 0;
    rows_in_batch INTEGER;
BEGIN
    LOOP
        SELECT process_result_batch(batch_size) INTO rows_in_batch;
        
        IF rows_in_batch = 0 THEN
            EXIT;
        END IF;
        
        total_processed := total_processed + rows_in_batch;
        RAISE NOTICE 'Processed % rows so far', total_processed;
    END LOOP;
    
    RAISE NOTICE 'Finished processing % total rows', total_processed;
END $$;
COMMIT;

-- Drop the batch processing function
DROP FUNCTION IF EXISTS process_result_batch(INTEGER);

-- Verify all rows were converted
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM games WHERE result_bits IS NULL) THEN
        RAISE EXCEPTION 'Some rows were not converted';
    END IF;
END $$;

-- Drop old column and rename new one
ALTER TABLE games DROP COLUMN result;
ALTER TABLE games RENAME COLUMN result_bits TO result;

-- Add constraint
ALTER TABLE games ADD CONSTRAINT result_check CHECK (result >= 0 AND result <= 3);

-- Create helper functions
CREATE OR REPLACE FUNCTION decode_result(result_bits INTEGER)
RETURNS TEXT AS $$
BEGIN
    RETURN CASE result_bits
        WHEN 1 THEN '1/2-1/2'
        WHEN 2 THEN '1-0'
        WHEN 3 THEN '0-1'
        ELSE '*'
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION encode_result(result_str TEXT)
RETURNS INTEGER AS $$
BEGIN
    RETURN CASE result_str
        WHEN '1/2-1/2' THEN 1
        WHEN '1-0' THEN 2
        WHEN '0-1' THEN 3
        ELSE 0
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create view
CREATE OR REPLACE VIEW games_with_result_str AS
SELECT 
    g.*,
    decode_result(result) as result_str
FROM games g;

-- Record migration
INSERT INTO schema_migrations (version) VALUES ('001_convert_result_to_bits');
