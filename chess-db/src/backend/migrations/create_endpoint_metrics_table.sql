-- Create endpoint metrics table
CREATE TABLE IF NOT EXISTS endpoint_metrics (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    response_size_bytes INTEGER,
    status_code INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    request_params JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_endpoint_metrics_endpoint ON endpoint_metrics(endpoint);
CREATE INDEX IF NOT EXISTS idx_endpoint_metrics_method ON endpoint_metrics(method);
CREATE INDEX IF NOT EXISTS idx_endpoint_metrics_created_at ON endpoint_metrics(created_at);
CREATE INDEX IF NOT EXISTS idx_endpoint_metrics_success ON endpoint_metrics(success);

$$ LANGUAGE plpgsql;
