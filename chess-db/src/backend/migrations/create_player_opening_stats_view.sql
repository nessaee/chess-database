-- Create materialized view for player opening statistics
CREATE MATERIALIZED VIEW player_opening_stats AS
WITH base_stats AS (
    SELECT 
        p.id as player_id,
        p.name as player_name,
        gom.opening_id,
        g.date,
        gom.game_move_length,
        gom.opening_move_length,
        -- Precalculate color and result in one pass
        CASE WHEN g.white_player_id = p.id THEN 1 ELSE 0 END as is_white,
        CASE
            WHEN (g.white_player_id = p.id AND g.result = '1-0') OR 
                 (g.black_player_id = p.id AND g.result = '0-1') THEN 1
            WHEN g.result = '1/2-1/2' THEN 0.5
            ELSE 0
        END as points,
        COALESCE(TO_CHAR(g.date, 'YYYY-MM'), '1900-01') as month
    FROM games g
    JOIN game_opening_matches gom ON g.id = gom.game_id
    JOIN players p ON p.id IN (g.white_player_id, g.black_player_id)
),
monthly_agg AS (
    SELECT 
        player_id,
        player_name,
        opening_id,
        month,
        COUNT(*) as games,
        SUM(points) as points,
        ROUND(AVG(points) * 100::numeric, 2) as win_rate
    FROM base_stats
    GROUP BY player_id, player_name, opening_id, month
),
trend_data_agg AS (
    SELECT 
        player_id,
        opening_id,
        jsonb_build_object(
            'months', COALESCE(jsonb_agg(DISTINCT month ORDER BY month DESC), '[]'::jsonb),
            'monthly_stats', COALESCE(
                jsonb_object_agg(
                    month,
                    jsonb_build_object(
                        'games', games,
                        'win_rate', win_rate
                    )
                ),
                '{}'::jsonb
            )
        ) as trend_data
    FROM monthly_agg
    GROUP BY player_id, opening_id
)
SELECT 
    bs.player_id,
    bs.player_name,
    bs.opening_id,
    COUNT(*) as total_games,
    ROUND(SUM(bs.points)::numeric, 0) as wins,
    SUM(CASE WHEN bs.points = 0.5 THEN 1 ELSE 0 END) as draws,
    SUM(CASE WHEN bs.points = 0 THEN 1 ELSE 0 END) as losses,
    ROUND(AVG(bs.game_move_length)::numeric, 2) as avg_game_length,
    ROUND(AVG(bs.opening_move_length)::numeric, 2) as avg_opening_length,
    SUM(bs.is_white) as white_games,
    COUNT(*) - SUM(bs.is_white) as black_games,
    MAX(bs.date) as last_played,
    ROUND(AVG(bs.points) * 100::numeric, 2) as win_rate,
    COALESCE(td.trend_data, jsonb_build_object(
        'months', '[]'::jsonb,
        'monthly_stats', '{}'::jsonb
    )) as trend_data
FROM base_stats bs
LEFT JOIN trend_data_agg td ON td.player_id = bs.player_id AND td.opening_id = bs.opening_id
GROUP BY bs.player_id, bs.player_name, bs.opening_id, td.trend_data;

-- Create index for faster lookups
CREATE INDEX idx_player_opening_stats_player_id ON player_opening_stats (player_id);
CREATE INDEX idx_player_opening_stats_player_name ON player_opening_stats (player_name);
CREATE INDEX idx_player_opening_stats_opening_id ON player_opening_stats (opening_id);
CREATE INDEX idx_player_opening_stats_total_games ON player_opening_stats (total_games DESC);
CREATE INDEX idx_player_opening_stats_win_rate ON player_opening_stats (win_rate DESC);

-- Create function to refresh the view
CREATE OR REPLACE FUNCTION refresh_player_opening_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY player_opening_stats;
END;
$$ LANGUAGE plpgsql;
