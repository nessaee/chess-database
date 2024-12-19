-- Initialize the refresh status for endpoint performance stats
INSERT INTO materialized_view_refresh_status (view_name, last_refresh, refresh_in_progress, partition_refreshed)
VALUES ('endpoint_performance_stats', NULL, FALSE, ARRAY[]::TEXT[])
ON CONFLICT (view_name) DO UPDATE
SET refresh_in_progress = FALSE,
    partition_refreshed = ARRAY[]::TEXT[];

-- Initialize refresh status for other materialized views
INSERT INTO materialized_view_refresh_status (view_name, last_refresh, refresh_in_progress, partition_refreshed)
VALUES 
    ('move_count_stats', NULL, FALSE, ARRAY[]::TEXT[]),
    ('game_opening_matches', NULL, FALSE, ARRAY[]::TEXT[]),
    ('player_opening_stats', NULL, FALSE, ARRAY[]::TEXT[])
ON CONFLICT (view_name) DO UPDATE
SET refresh_in_progress = FALSE,
    partition_refreshed = ARRAY[]::TEXT[];
