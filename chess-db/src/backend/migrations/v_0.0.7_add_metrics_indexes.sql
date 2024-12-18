-- Add indexes to improve metrics query performance

-- Indexes for the games table
CREATE INDEX IF NOT EXISTS idx_games_players ON games(white_player_id, black_player_id);
CREATE INDEX IF NOT EXISTS idx_games_date ON games(date);
CREATE INDEX IF NOT EXISTS idx_games_result ON games(result);
CREATE INDEX IF NOT EXISTS idx_games_eco ON games(eco);

-- Indexes for endpoint_metrics table
CREATE INDEX IF NOT EXISTS idx_endpoint_metrics_endpoint ON endpoint_metrics(endpoint, method);
CREATE INDEX IF NOT EXISTS idx_endpoint_metrics_created ON endpoint_metrics(created_at);
CREATE INDEX IF NOT EXISTS idx_endpoint_metrics_status ON endpoint_metrics(status_code, success);

-- Indexes for game_opening_matches table
CREATE INDEX IF NOT EXISTS idx_game_opening_matches_game ON game_opening_matches(game_id);
CREATE INDEX IF NOT EXISTS idx_game_opening_matches_opening ON game_opening_matches(opening_id);

-- Index for move_count_stats
CREATE INDEX IF NOT EXISTS idx_move_count_stats_moves ON move_count_stats(actual_full_moves);

-- Index for player_opening_stats
CREATE INDEX IF NOT EXISTS idx_player_opening_stats_player ON player_opening_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_opening_stats_opening ON player_opening_stats(opening_id);
CREATE INDEX IF NOT EXISTS idx_player_opening_stats_last_played ON player_opening_stats(last_played);
