---
layout: default
title: Database Optimizations
parent: Backend
nav_order: 3
---

# Database Optimizations

{: .fs-9 }
Comprehensive guide to database partitioning, materialized views, and indexing strategies.

{: .fs-6 .fw-300 }
The Chess Database uses advanced PostgreSQL features to optimize performance and storage efficiency.

---

## Table Partitioning

### Games Table Partitioning
The games table is partitioned by game result and rating range to optimize query performance:

```sql
CREATE TABLE games (
    id UUID PRIMARY KEY,
    white_player_id UUID,
    black_player_id UUID,
    white_elo INTEGER,
    black_elo INTEGER,
    date DATE,
    eco VARCHAR(3),
    moves BYTEA,
    result SMALLINT
) PARTITION BY RANGE (white_elo, black_elo);
```

Partition ranges:
- Low rated games: 0-1500
- Mid rated games: 1501-2000
- High rated games: 2001-3000
- Master games: >3000

## Materialized Views

### 1. Move Count Statistics
```sql
CREATE MATERIALIZED VIEW move_count_stats AS
SELECT 
    actual_full_moves,
    COUNT(*) as number_of_games,
    AVG(LENGTH(moves)) as avg_bytes,
    partition_distribution
FROM games
GROUP BY actual_full_moves, partition_distribution;
```

Purpose:
- Track move count distribution
- Monitor storage efficiency
- Analyze game length patterns

### 2. Game Opening Matches
```sql
CREATE MATERIALIZED VIEW game_opening_matches AS
SELECT 
    g.id as game_id,
    o.id as opening_id,
    LENGTH(g.moves) as game_move_length,
    LENGTH(o.moves) as opening_move_length,
    g.partition_num
FROM games g
JOIN openings o ON g.eco = o.eco;
```

Purpose:
- Fast opening classification
- Opening popularity analysis
- Move sequence matching

### 3. Player Opening Statistics
```sql
CREATE MATERIALIZED VIEW player_opening_stats AS
SELECT 
    p.id as player_id,
    p.name as player_name,
    o.id as opening_id,
    COUNT(*) as total_games,
    SUM(CASE WHEN g.result = 1 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN g.result = 0 THEN 1 ELSE 0 END) as draws,
    SUM(CASE WHEN g.result = -1 THEN 1 ELSE 0 END) as losses,
    AVG(LENGTH(g.moves)) as avg_game_length,
    AVG(LENGTH(o.moves)) as avg_opening_length
FROM games g
JOIN players p ON g.white_player_id = p.id OR g.black_player_id = p.id
JOIN openings o ON g.eco = o.eco
GROUP BY p.id, p.name, o.id;
```

Purpose:
- Player performance analysis
- Opening repertoire tracking
- Win-rate statistics

### 4. Endpoint Performance Stats
```sql
CREATE MATERIALIZED VIEW endpoint_performance_stats AS
SELECT 
    endpoint,
    method,
    COUNT(*) as total_calls,
    SUM(CASE WHEN status_code < 400 THEN 1 ELSE 0 END) as successful_calls,
    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count,
    AVG(response_time_ms) as avg_response_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) as p99_response_time_ms,
    MAX(response_time_ms) as max_response_time_ms,
    MIN(response_time_ms) as min_response_time_ms,
    SUM(CASE WHEN status_code < 400 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate,
    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as error_rate,
    AVG(response_size_bytes) as avg_response_size_bytes,
    MAX(response_size_bytes) as max_response_size_bytes,
    MIN(response_size_bytes) as min_response_size_bytes
FROM endpoint_metrics
GROUP BY endpoint, method;
```

Purpose:
- API performance monitoring
- Error rate tracking
- Response time analysis

## Indexes

### Primary Indexes
```sql
-- Games table
CREATE INDEX idx_games_white_player ON games(white_player_id);
CREATE INDEX idx_games_black_player ON games(black_player_id);
CREATE INDEX idx_games_eco ON games(eco);
CREATE INDEX idx_games_date ON games(date);

-- Players table
CREATE INDEX idx_players_name ON players(name);

-- Openings table
CREATE INDEX idx_openings_eco ON openings(eco);
CREATE INDEX idx_openings_name ON openings(name);
```

### Performance Indexes
```sql
-- Endpoint metrics
CREATE INDEX idx_endpoint_metrics_timestamp ON endpoint_metrics(created_at);
CREATE INDEX idx_endpoint_metrics_endpoint ON endpoint_metrics(endpoint);
CREATE INDEX idx_endpoint_metrics_status ON endpoint_metrics(status_code);

-- Move statistics
CREATE INDEX idx_move_stats_count ON move_count_stats(actual_full_moves);
CREATE INDEX idx_move_stats_games ON move_count_stats(number_of_games);
```

## Refresh Strategy

### Materialized View Management
```sql
CREATE TABLE materialized_view_refresh_status (
    view_name TEXT PRIMARY KEY,
    last_refresh TIMESTAMP,
    refresh_in_progress BOOLEAN DEFAULT FALSE,
    partition_refreshed INTEGER
);
```

Refresh schedule:
- move_count_stats: Daily
- game_opening_matches: Hourly
- player_opening_stats: Daily
- endpoint_performance_stats: Every 15 minutes

## Performance Benefits

1. **Query Optimization**
   - Partitioned tables reduce scan size
   - Materialized views pre-compute expensive joins
   - Indexes speed up common lookups

2. **Storage Efficiency**
   - Move encoding reduces storage requirements
   - Partitioning enables better compression
   - Selective indexing minimizes overhead

3. **Monitoring Capabilities**
   - Real-time performance metrics
   - Resource usage tracking
   - Query pattern analysis

## Maintenance

Regular maintenance tasks:
1. Refresh materialized views on schedule
2. Update table statistics
3. Reindex when necessary
4. Monitor partition growth
5. Archive old endpoint metrics

## Best Practices

1. **Query Guidelines**
   - Use appropriate indexes
   - Leverage materialized views
   - Consider partition pruning

2. **Data Management**
   - Regular view refreshes
   - Monitor storage usage
   - Archive old data

3. **Performance Monitoring**
   - Track query performance
   - Monitor view refresh times
   - Analyze index usage
