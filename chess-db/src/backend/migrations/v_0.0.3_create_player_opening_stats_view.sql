-- Drop existing view and indexes if they exist
DROP MATERIALIZED VIEW IF EXISTS player_opening_stats CASCADE;

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
            WHEN (g.white_player_id = p.id AND g.result = 1) OR  -- White wins
                 (g.black_player_id = p.id AND g.result = 0) THEN 1  -- Black wins
            WHEN g.result = 2 THEN 0.5  -- Draw
            ELSE 0  -- Unknown or loss
        END as points,
        COALESCE(TO_CHAR(g.date, 'YYYY-MM'), '1900-01') as month,
        gom.partition_num
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
        partition_num,
        COUNT(*) as games,
        SUM(points) as points,
        ROUND(AVG(points) * 100::numeric, 2) as win_rate
    FROM base_stats
    GROUP BY player_id, player_name, opening_id, month, partition_num
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
            ),
            'partition_stats', COALESCE(
                jsonb_object_agg(
                    partition_num::text,
                    jsonb_build_object(
                        'games', COUNT(*),
                        'win_rate', ROUND(AVG(win_rate), 2)
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
    SUM(CASE WHEN bs.points = 1 THEN 1 ELSE 0 END) as wins,
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
        'monthly_stats', '{}'::jsonb,
        'partition_stats', '{}'::jsonb
    )) as trend_data,
    jsonb_build_object(
        'partition_distribution',
        jsonb_object_agg(
            bs.partition_num::text,
            COUNT(*)
        )
    ) as partition_info
FROM base_stats bs
LEFT JOIN trend_data_agg td ON td.player_id = bs.player_id AND td.opening_id = bs.opening_id
GROUP BY bs.player_id, bs.player_name, bs.opening_id, td.trend_data;

-- Create efficient indexes
CREATE UNIQUE INDEX idx_player_opening_stats_player_opening 
ON player_opening_stats (player_id, opening_id);

CREATE INDEX idx_player_opening_stats_player_name 
ON player_opening_stats (player_name)
INCLUDE (total_games, win_rate);

CREATE INDEX idx_player_opening_stats_opening_id 
ON player_opening_stats (opening_id)
INCLUDE (total_games, win_rate);

CREATE INDEX idx_player_opening_stats_metrics 
ON player_opening_stats (total_games DESC, win_rate DESC)
INCLUDE (player_name, player_id);

-- Create function to refresh the view
CREATE OR REPLACE FUNCTION refresh_player_opening_stats()
RETURNS void AS $$
BEGIN
    -- Use CONCURRENTLY for zero-downtime refresh
    REFRESH MATERIALIZED VIEW CONCURRENTLY player_opening_stats;
END;
$$ LANGUAGE plpgsql;

-- Create function to refresh stats for specific partition
CREATE OR REPLACE FUNCTION refresh_player_opening_stats_partition(p_num integer)
RETURNS void AS $$
BEGIN
    -- Refresh stats only for games in the specified partition
    WITH partition_games AS (
        SELECT 
            p.id as player_id,
            p.name as player_name,
            gom.opening_id,
            g.date,
            gom.game_move_length,
            gom.opening_move_length,
            CASE WHEN g.white_player_id = p.id THEN 1 ELSE 0 END as is_white,
            CASE
                WHEN (g.white_player_id = p.id AND g.result = 1) OR
                     (g.black_player_id = p.id AND g.result = 0) THEN 1
                WHEN g.result = 2 THEN 0.5
                ELSE 0
            END as points
        FROM games g
        JOIN game_opening_matches gom ON g.id = gom.game_id
        JOIN players p ON p.id IN (g.white_player_id, g.black_player_id)
        WHERE g.id % 8 = p_num
    )
    -- Update stats for affected player-opening pairs
    UPDATE player_opening_stats pos
    SET 
        total_games = subq.total_games,
        wins = subq.wins,
        draws = subq.draws,
        losses = subq.losses,
        avg_game_length = subq.avg_game_length,
        avg_opening_length = subq.avg_opening_length,
        white_games = subq.white_games,
        black_games = subq.black_games,
        win_rate = subq.win_rate
    FROM (
        SELECT 
            player_id,
            opening_id,
            COUNT(*) as total_games,
            SUM(CASE WHEN points = 1 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN points = 0.5 THEN 1 ELSE 0 END) as draws,
            SUM(CASE WHEN points = 0 THEN 1 ELSE 0 END) as losses,
            ROUND(AVG(game_move_length)::numeric, 2) as avg_game_length,
            ROUND(AVG(opening_move_length)::numeric, 2) as avg_opening_length,
            SUM(is_white) as white_games,
            COUNT(*) - SUM(is_white) as black_games,
            ROUND(AVG(points) * 100::numeric, 2) as win_rate
        FROM partition_games
        GROUP BY player_id, opening_id
    ) subq
    WHERE pos.player_id = subq.player_id
    AND pos.opening_id = subq.opening_id;
END;
$$ LANGUAGE plpgsql;
