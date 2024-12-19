-- Create endpoint metrics table with partitioning
CREATE TABLE IF NOT EXISTS endpoint_metrics (
    id BIGSERIAL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    response_size_bytes INTEGER,
    status_code SMALLINT NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    request_params JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (created_at, id)
) PARTITION BY RANGE (created_at);

-- Create partitions for the last 30 days and future 30 days
DO $$
DECLARE
    partition_start DATE;
    partition_end DATE;
    partition_name TEXT;
BEGIN
    -- Create partitions for past 30 days
    FOR i IN 0..29 LOOP
        partition_start := CURRENT_DATE - (i || ' days')::INTERVAL;
        partition_end := partition_start + '1 day'::INTERVAL;
        partition_name := 'endpoint_metrics_p' || TO_CHAR(partition_start, 'YYYYMMDD');
        
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF endpoint_metrics 
            FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            partition_start,
            partition_end
        );
    END LOOP;
    
    -- Create partitions for next 30 days
    FOR i IN 1..30 LOOP
        partition_start := CURRENT_DATE + (i - 1 || ' days')::INTERVAL;
        partition_end := partition_start + '1 day'::INTERVAL;
        partition_name := 'endpoint_metrics_p' || TO_CHAR(partition_start, 'YYYYMMDD');
        
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF endpoint_metrics 
            FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            partition_start,
            partition_end
        );
    END LOOP;
END $$;

-- Create function to manage partitions
CREATE OR REPLACE FUNCTION maintain_endpoint_metrics_partitions()
RETURNS void AS $$
DECLARE
    partition_date DATE;
    partition_name TEXT;
BEGIN
    -- Create partition for 30 days in the future
    partition_date := CURRENT_DATE + '30 days'::INTERVAL;
    partition_name := 'endpoint_metrics_p' || TO_CHAR(partition_date, 'YYYYMMDD');
    
    -- Create new partition if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_class c 
        JOIN pg_namespace n ON n.oid = c.relnamespace 
        WHERE c.relname = partition_name
    ) THEN
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF endpoint_metrics 
            FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            partition_date,
            partition_date + '1 day'::INTERVAL
        );
    END IF;
    
    -- Drop partitions older than 30 days
    FOR partition_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'endpoint_metrics_p%'
        AND TO_DATE(RIGHT(tablename, 8), 'YYYYMMDD') < CURRENT_DATE - '30 days'::INTERVAL
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I', partition_name);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create efficient indexes on each partition
CREATE OR REPLACE FUNCTION create_endpoint_metrics_partition_indexes()
RETURNS void AS $$
DECLARE
    partition_name TEXT;
BEGIN
    FOR partition_name IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'endpoint_metrics_p%'
    LOOP
        -- Create indexes if they don't exist
        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS %I ON %I (endpoint, method) 
            INCLUDE (response_time_ms, success)',
            'idx_' || partition_name || '_endpoint_method',
            partition_name
        );
        
        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS %I ON %I (created_at) 
            INCLUDE (response_time_ms, status_code)',
            'idx_' || partition_name || '_created_at',
            partition_name
        );
        
        EXECUTE format(
            'CREATE INDEX IF NOT EXISTS %I ON %I (success) 
            WHERE NOT success',
            'idx_' || partition_name || '_errors',
            partition_name
        );
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Schedule partition maintenance
CREATE EXTENSION IF NOT EXISTS pg_cron;

SELECT cron.schedule('maintain_endpoint_metrics', '0 0 * * *', 'SELECT maintain_endpoint_metrics_partitions()');
SELECT cron.schedule('create_partition_indexes', '5 0 * * *', 'SELECT create_endpoint_metrics_partition_indexes()');
