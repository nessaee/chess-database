-- Rollback: Convert game results back to strings
-- Version: 001

DO $$ 
BEGIN
    -- Check if this migration has been applied
    IF NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '001_convert_result_to_bits') THEN
        RAISE NOTICE 'Migration 001_convert_result_to_bits has not been applied, nothing to rollback';
        RETURN;
    END IF;

    -- Perform the rollback
    -- Add temporary column for string results
    ALTER TABLE games ADD COLUMN result_str VARCHAR(10);

    -- Convert bits back to strings
    UPDATE games
    SET result_str = decode_result(result);

    -- Drop the bits column and rename string column
    ALTER TABLE games DROP COLUMN result;
    ALTER TABLE games RENAME COLUMN result_str TO result;

    -- Drop the helper functions and view
    DROP FUNCTION IF EXISTS decode_result;
    DROP FUNCTION IF EXISTS encode_result;
    DROP VIEW IF EXISTS games_with_result_str;

    -- Remove the migration record
    DELETE FROM schema_migrations WHERE version = '001_convert_result_to_bits';
    RAISE NOTICE 'Migration 001_convert_result_to_bits rolled back successfully';

EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error rolling back migration: %', SQLERRM;
    RAISE;
END $$;
