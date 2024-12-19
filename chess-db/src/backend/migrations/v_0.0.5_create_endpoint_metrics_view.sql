-- Create a table to track the last refresh time of materialized views
CREATE TABLE IF NOT EXISTS materialized_view_refresh_status (
    view_name TEXT PRIMARY KEY,
    last_refresh TIMESTAMP WITH TIME ZONE,
    refresh_in_progress BOOLEAN DEFAULT FALSE,
    partition_refreshed TEXT[] DEFAULT ARRAY[]::TEXT[]
);

-- Create materialized view for endpoint performance statistics
CREATE MATERIALIZED VIEW endpoint_performance_stats AS
WITH partition_stats AS (
    SELECT
        endpoint,
        method,
        tablename as partition_name,
        COUNT(*) as total_calls,
        COUNT(CASE WHEN success THEN 1 END) as successful_calls,
        COUNT(CASE WHEN NOT success THEN 1 END) as error_count,
        AVG(CASE WHEN success THEN response_time_ms END) as avg_response_time_ms,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time_ms,
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) as p99_response_time_ms,
        MAX(response_time_ms) as max_response_time_ms,
        MIN(response_time_ms) as min_response_time_ms,
        ROUND(COUNT(CASE WHEN success THEN 1 END)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2) as success_rate,
        AVG(response_size_bytes) as avg_response_size_bytes,
        MAX(response_size_bytes) as max_response_size_bytes,
        MIN(response_size_bytes) as min_response_size_bytes,
        array_agg(DISTINCT error_message) FILTER (WHERE error_message IS NOT NULL) as error_messages
    FROM endpoint_metrics em
    JOIN pg_tables pt ON pt.tablename LIKE 'endpoint_metrics_p%'
        AND em.created_at >= TO_TIMESTAMP(RIGHT(pt.tablename, 8), 'YYYYMMDD')
        AND em.created_at < TO_TIMESTAMP(RIGHT(pt.tablename, 8), 'YYYYMMDD') + INTERVAL '1 day'
    WHERE em.created_at >= NOW() - INTERVAL '24 hours'
    GROUP BY endpoint, method, tablename
),
unnested_errors AS (
    SELECT
        endpoint,
        method,
        total_calls,
        successful_calls,
        error_count,
        avg_response_time_ms,
        p95_response_time_ms,
        p99_response_time_ms,
        max_response_time_ms,
        min_response_time_ms,
        success_rate,
        avg_response_size_bytes,
        max_response_size_bytes,
        min_response_size_bytes,
        error_messages,
        partition_name,
        e.error_msg
    FROM partition_stats ps
    LEFT JOIN LATERAL unnest(ps.error_messages) AS e(error_msg) ON true
),
endpoint_stats AS (
    SELECT
        endpoint,
        method,
        SUM(total_calls) as total_calls,
        SUM(successful_calls) as successful_calls,
        SUM(error_count) as error_count,
        AVG(avg_response_time_ms) as avg_response_time_ms,
        MAX(p95_response_time_ms) as p95_response_time_ms,
        MAX(p99_response_time_ms) as p99_response_time_ms,
        MAX(max_response_time_ms) as max_response_time_ms,
        MIN(min_response_time_ms) as min_response_time_ms,
        ROUND(SUM(successful_calls)::NUMERIC / NULLIF(SUM(total_calls), 0) * 100, 2) as success_rate,
        ROUND(SUM(error_count)::NUMERIC / NULLIF(SUM(total_calls), 0) * 100, 2) as error_rate,
        AVG(avg_response_size_bytes) as avg_response_size_bytes,
        MAX(max_response_size_bytes) as max_response_size_bytes,
        MIN(min_response_size_bytes) as min_response_size_bytes,
        array_agg(DISTINCT error_msg) FILTER (WHERE error_msg IS NOT NULL) as error_messages,
        jsonb_object_agg(
            partition_name,
            jsonb_build_object(
                'calls', total_calls,
                'success_rate', success_rate,
                'avg_response_time', ROUND(avg_response_time_ms::NUMERIC, 2)
            )
        ) as partition_stats
    FROM unnested_errors
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
    error_messages,
    partition_stats
FROM endpoint_stats
ORDER BY total_calls DESC;

-- Create unique index for efficient refreshing
CREATE UNIQUE INDEX IF NOT EXISTS idx_endpoint_performance_stats 
ON endpoint_performance_stats(endpoint, method);

-- Function to refresh the materialized view with partition-aware status tracking
CREATE OR REPLACE FUNCTION refresh_endpoint_performance_stats()
RETURNS BOOLEAN AS $$
DECLARE
    last_refresh_time TIMESTAMP WITH TIME ZONE;
    latest_metric_time TIMESTAMP WITH TIME ZONE;
    refresh_needed BOOLEAN := FALSE;
    partition_name TEXT;
    refreshed_partitions TEXT[];
BEGIN
    -- Get the last refresh time and refreshed partitions
    SELECT last_refresh, partition_refreshed 
    INTO last_refresh_time, refreshed_partitions
    FROM materialized_view_refresh_status 
    WHERE view_name = 'endpoint_performance_stats';

    -- If no record exists, this is the first refresh
    IF last_refresh_time IS NULL THEN
        refresh_needed := TRUE;
    ELSE
        -- Check for new data in any partition
        SELECT MAX(created_at) INTO latest_metric_time
        FROM endpoint_metrics
        WHERE created_at > last_refresh_time;

        IF latest_metric_time IS NOT NULL THEN
            refresh_needed := TRUE;
        END IF;
    END IF;

    -- If refresh is needed, perform it
    IF refresh_needed THEN
        -- Mark refresh as in progress
        INSERT INTO materialized_view_refresh_status (view_name, refresh_in_progress)
        VALUES ('endpoint_performance_stats', TRUE)
        ON CONFLICT (view_name) DO UPDATE
        SET refresh_in_progress = TRUE,
            last_refresh = NULL;

        -- Refresh the materialized view
        REFRESH MATERIALIZED VIEW CONCURRENTLY endpoint_performance_stats;

        -- Update refresh status
        UPDATE materialized_view_refresh_status
        SET last_refresh = NOW(),
            refresh_in_progress = FALSE
        WHERE view_name = 'endpoint_performance_stats';

        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;
