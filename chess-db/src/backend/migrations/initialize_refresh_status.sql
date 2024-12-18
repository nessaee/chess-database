-- Initialize the refresh status for endpoint performance stats
INSERT INTO materialized_view_refresh_status (view_name, last_refresh, refresh_in_progress)
VALUES ('endpoint_performance_stats', NULL, FALSE)
ON CONFLICT (view_name) DO UPDATE
SET refresh_in_progress = FALSE;
