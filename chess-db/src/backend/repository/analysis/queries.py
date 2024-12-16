# repository/analysis/queries.py

MOVE_COUNT_QUERY = """
    WITH game_moves_analysis AS (
        SELECT
            (octet_length(moves) - 19) / 2 as actual_full_moves,
            get_byte(moves, 17) << 8 | get_byte(moves, 18) as stored_move_count,
            result,
            octet_length(moves) as total_bytes
        FROM games
        WHERE moves IS NOT NULL
            AND octet_length(moves) >= 19
    )
    SELECT
        actual_full_moves,
        COUNT(*) as number_of_games,
        ROUND(AVG(total_bytes)::numeric, 2) as avg_bytes,
        string_agg(DISTINCT result, ', ' ORDER BY result) as results,
        MIN(stored_move_count) as min_stored_count,
        MAX(stored_move_count) as max_stored_count,
        ROUND(AVG(stored_move_count)::numeric, 2) as avg_stored_count
    FROM game_moves_analysis
    WHERE actual_full_moves >= 0
        AND actual_full_moves <= 500
    GROUP BY actual_full_moves
    ORDER BY actual_full_moves ASC
"""

PLAYER_OPENING_QUERY = """
    WITH player_games AS (
        SELECT
            g.*,
            CASE 
                WHEN white_player_id = :player_id THEN 'white'
                ELSE 'black'
            END as player_color,
            CASE
                WHEN (white_player_id = :player_id AND result = '1-0') OR
                     (black_player_id = :player_id AND result = '0-1')
                THEN 'win'
                WHEN result = '1/2-1/2' THEN 'draw'
                ELSE 'loss'
            END as outcome,
            (octet_length(moves) - 19) / 2 as move_count
        FROM games g
        WHERE (white_player_id = :player_id OR black_player_id = :player_id)
            {% if start_date %}
            AND date >= :start_date::date
            {% endif %}
            {% if end_date %}
            AND date <= :end_date::date
            {% endif %}
    )
    SELECT
        eco,
        o.name as opening_name,
        COUNT(*) as total_games,
        SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN outcome = 'draw' THEN 1 ELSE 0 END) as draws,
        SUM(CASE WHEN outcome = 'loss' THEN 1 ELSE 0 END) as losses,
        ROUND(
            AVG(CASE 
                WHEN outcome = 'win' THEN 1.0
                WHEN outcome = 'draw' THEN 0.5
                ELSE 0.0 
            END) * 100,
            2
        ) as win_rate,
        ROUND(AVG(move_count), 2) as avg_game_length
    FROM player_games g
    LEFT JOIN openings o ON g.eco = o.eco_code
    WHERE eco IS NOT NULL
    GROUP BY eco, o.name
    HAVING COUNT(*) >= :min_games
    ORDER BY total_games DESC, win_rate DESC
"""

PLAYER_PERFORMANCE_QUERY = """
    WITH player_games AS (
        SELECT
            g.*,
            CASE
                WHEN white_player_id = :player_id THEN white_elo
                ELSE black_elo
            END as player_rating,
            CASE
                WHEN (white_player_id = :player_id AND result = '1-0') OR
                     (black_player_id = :player_id AND result = '0-1')
                THEN 'win'
                WHEN result = '1/2-1/2' THEN 'draw'
                ELSE 'loss'
            END as outcome,
            CASE 
                WHEN white_player_id = :player_id THEN 'white'
                ELSE 'black'
            END as player_color,
            (octet_length(moves) - 19) / 2 as move_count
        FROM games g
        WHERE (white_player_id = :player_id OR black_player_id = :player_id)
            {% if start_date %}
            AND date >= :start_date::date
            {% endif %}
            {% if end_date %}
            AND date <= :end_date::date
            {% endif %}
    )
    SELECT
        date_trunc(:time_group, date) as period,
        COUNT(*) as games_played,
        SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN outcome = 'loss' THEN 1 ELSE 0 END) as losses,
        SUM(CASE WHEN outcome = 'draw' THEN 1 ELSE 0 END) as draws,
        ROUND(AVG(CASE WHEN outcome = 'win' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate,
        ROUND(AVG(move_count), 2) as avg_moves,
        SUM(CASE WHEN player_color = 'white' THEN 1 ELSE 0 END) as white_games,
        SUM(CASE WHEN player_color = 'black' THEN 1 ELSE 0 END) as black_games,
        ROUND(AVG(player_rating), 0) as avg_rating
    FROM player_games
    GROUP BY date_trunc(:time_group, date)
    ORDER BY period DESC
"""

# Continuing the DATABASE_METRICS_QUERY...
DATABASE_METRICS_QUERY = """
    WITH database_stats AS (
        SELECT
            (SELECT COUNT(*) FROM games) as total_games,
            (SELECT COUNT(*) FROM players) as total_players,
            (SELECT COUNT(DISTINCT eco) FROM games WHERE eco IS NOT NULL) as total_openings,
            pg_database_size(current_database()) / (1024 * 1024.0) as storage_mb,
            (
                SELECT ROUND(AVG(total_exec_time)::numeric, 2)
                FROM pg_stat_statements
                WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
            ) as avg_query_time,
            (
                SELECT ROUND(SUM(calls)::numeric / 
                    EXTRACT(epoch FROM NOW() - stats_reset), 2)
                FROM pg_stat_database
                WHERE datname = current_database()
            ) as queries_per_second,
            (
                SELECT ROUND(
                    (heap_blks_hit::float / NULLIF(heap_blks_hit + heap_blks_read, 0)) * 100,
                    2
                )
                FROM pg_statio_user_tables
            ) as cache_hit_ratio
    ),
    growth_metrics AS (
        SELECT json_build_object(
            'daily_increase', ROUND(AVG(daily_games), 2),
            'monthly_increase', ROUND(AVG(monthly_games), 2),
            'storage_growth', ROUND(AVG(storage_increase), 2)
        ) as growth_trend
        FROM (
            SELECT
                date_trunc('day', date) as day,
                COUNT(*) as daily_games,
                SUM(COUNT(*)) OVER (
                    ORDER BY date_trunc('day', date)
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                ) as monthly_games,
                AVG(octet_length(moves)) as storage_increase
            FROM games
            WHERE date >= NOW() - INTERVAL '30 days'
            GROUP BY date_trunc('day', date)
        ) daily_stats
    ),
    query_stats AS (
        SELECT json_agg(query_perf) as query_performance
        FROM (
            SELECT json_build_object(
                'query_type', LEFT(query, 50),
                'calls', calls,
                'total_time', ROUND(total_exec_time::numeric, 2),
                'avg_time', ROUND((total_exec_time / calls)::numeric, 2),
                'rows_processed', rows
            ) as query_perf
            FROM pg_stat_statements
            WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
            ORDER BY total_exec_time DESC
            LIMIT 10
        ) top_queries
    ),
    index_stats AS (
        SELECT
            ROUND(
                AVG(100 - (100 * COALESCE(idx_scan, 0) / 
                    NULLIF(seq_scan + idx_scan, 0)))::numeric,
                2
            ) as index_health
        FROM pg_stat_user_tables
    ),
    replication_stats AS (
        SELECT
            EXTRACT(epoch FROM (now() - pg_last_xact_replay_timestamp())) as replication_lag
        FROM pg_stat_replication
        WHERE state = 'streaming'
    ),
    capacity_metrics AS (
        SELECT
            ROUND((pg_database_size(current_database())::float / 
                pg_tablespace_size('pg_default') * 100)::numeric, 2
            ) as capacity_used,
            CASE
                WHEN growth_rate > 0 THEN
                    now() + ((available_space / growth_rate) * INTERVAL '1 day')
                ELSE NULL
            END as capacity_date
        FROM (
            SELECT
                pg_tablespace_size('pg_default') - pg_database_size(current_database()) 
                    as available_space,
                (
                    SELECT (MAX(total_bytes) - MIN(total_bytes))::float / 30
                    FROM (
                        SELECT date_trunc('day', date) as day,
                            SUM(octet_length(moves)) as total_bytes
                        FROM games
                        WHERE date >= NOW() - INTERVAL '30 days'
                        GROUP BY date_trunc('day', date)
                    ) daily_growth
                ) as growth_rate
        ) space_metrics
    )
    SELECT
        s.total_games,
        s.total_players,
        s.total_openings,
        s.storage_mb,
        s.avg_query_time,
        s.queries_per_second,
        s.cache_hit_ratio,
        g.growth_trend,
        q.query_performance,
        i.index_health,
        r.replication_lag,
        c.capacity_used,
        c.capacity_date
    FROM database_stats s
    CROSS JOIN growth_metrics g
    CROSS JOIN query_stats q
    CROSS JOIN index_stats i
    CROSS JOIN replication_stats r
    CROSS JOIN capacity_metrics c
"""