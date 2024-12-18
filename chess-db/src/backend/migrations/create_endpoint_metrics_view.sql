-- Create a table to track the last refresh time of materialized views
CREATE TABLE IF NOT EXISTS materialized_view_refresh_status (
    view_name TEXT PRIMARY KEY,
    last_refresh TIMESTAMP WITH TIME ZONE,
    refresh_in_progress BOOLEAN DEFAULT FALSE
);

-- Create materialized view for endpoint performance statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS endpoint_performance_stats AS
WITH endpoint_stats AS (
    SELECT
        endpoint,
        method,
        COUNT(*) as total_calls,
        COUNT(CASE WHEN success THEN 1 END) as successful_calls,
        COUNT(CASE WHEN NOT success THEN 1 END) as error_count,
        AVG(CASE WHEN success THEN response_time_ms END) as avg_response_time_ms,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time_ms,
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) as p99_response_time_ms,
        MAX(response_time_ms) as max_response_time_ms,
        MIN(response_time_ms) as min_response_time_ms,
        ROUND(COUNT(CASE WHEN success THEN 1 END)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2) as success_rate,
        ROUND(COUNT(CASE WHEN NOT success THEN 1 END)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2) as error_rate,
        AVG(response_size_bytes) as avg_response_size_bytes,
        MAX(response_size_bytes) as max_response_size_bytes,
        MIN(response_size_bytes) as min_response_size_bytes,
        array_agg(DISTINCT error_message) FILTER (WHERE error_message IS NOT NULL) as error_messages
    FROM endpoint_metrics
    WHERE created_at >= NOW() - INTERVAL '24 hours'
    GROUP BY endpoint, method
)
SELECT 
    endpoint,
    method,
    total_calls,
    successful_calls,
    error_count,
    ROUND(avg_response_time_ms::NUMERIC, 2) as avg_response_time_ms,
    ROUND(p95_response_time_ms::NUMERIC, 2) as p95_response_time_ms,
    ROUND(p99_response_time_ms::NUMERIC, 2) as p99_response_time_ms,
    ROUND(max_response_time_ms::NUMERIC, 2) as max_response_time_ms,
    ROUND(min_response_time_ms::NUMERIC, 2) as min_response_time_ms,
    success_rate,
    error_rate,
    ROUND(avg_response_size_bytes::NUMERIC, 2) as avg_response_size_bytes,
    max_response_size_bytes,
    min_response_size_bytes,
    error_messages
FROM endpoint_stats
ORDER BY total_calls DESC;

-- Create index on endpoint_metrics created_at for efficient filtering
CREATE INDEX IF NOT EXISTS idx_endpoint_metrics_created_at ON endpoint_metrics(created_at);

-- Create unique index for efficient refreshing
CREATE UNIQUE INDEX IF NOT EXISTS idx_endpoint_performance_stats ON endpoint_performance_stats(endpoint, method);

-- Function to refresh the materialized view with status tracking
CREATE OR REPLACE FUNCTION refresh_endpoint_performance_stats()
RETURNS BOOLEAN AS $$
DECLARE
    last_refresh_time TIMESTAMP WITH TIME ZONE;
    latest_metric_time TIMESTAMP WITH TIME ZONE;
    refresh_needed BOOLEAN := FALSE;
BEGIN
    -- Get the last refresh time
    SELECT last_refresh INTO last_refresh_time
    FROM materialized_view_refresh_status
    WHERE view_name = 'endpoint_performance_stats';

    -- Get the latest metric timestamp
    SELECT MAX(created_at) INTO latest_metric_time
    FROM endpoint_metrics;

    -- Check if refresh is needed (if no previous refresh or new data exists)
    IF last_refresh_time IS NULL OR 
       latest_metric_time > last_refresh_time OR 
       last_refresh_time < NOW() - INTERVAL '1 hour' THEN
        refresh_needed := TRUE;
    END IF;

    -- Only refresh if needed and no refresh is in progress
    IF refresh_needed THEN
        -- Try to acquire refresh lock
        UPDATE materialized_view_refresh_status
        SET refresh_in_progress = TRUE
        WHERE view_name = 'endpoint_performance_stats'
        AND (refresh_in_progress = FALSE OR last_refresh < NOW() - INTERVAL '5 minutes');

        IF FOUND THEN
            BEGIN
                -- Refresh the view
                REFRESH MATERIALIZED VIEW CONCURRENTLY endpoint_performance_stats;
                
                -- Update refresh status
                INSERT INTO materialized_view_refresh_status (view_name, last_refresh, refresh_in_progress)
                VALUES ('endpoint_performance_stats', NOW(), FALSE)
                ON CONFLICT (view_name) DO UPDATE
                SET last_refresh = NOW(),
                    refresh_in_progress = FALSE;
                
                RETURN TRUE;
            EXCEPTION WHEN OTHERS THEN
                -- Reset refresh_in_progress on error
                UPDATE materialized_view_refresh_status
                SET refresh_in_progress = FALSE
                WHERE view_name = 'endpoint_performance_stats';
                RAISE;
            END;
        END IF;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Initialize the refresh status
INSERT INTO materialized_view_refresh_status (view_name, last_refresh, refresh_in_progress)
VALUES ('endpoint_performance_stats', NULL, FALSE)
ON CONFLICT (view_name) DO NOTHING;
