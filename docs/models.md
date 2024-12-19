# Data Models

## Core Models

### Player
```sql
CREATE TABLE players (
    id UUID PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    rating INTEGER,
    join_date TIMESTAMP,
    last_active TIMESTAMP,
    total_games INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0
);
```

### Game
```sql
CREATE TABLE games (
    id UUID PRIMARY KEY,
    white_player_id UUID REFERENCES players(id),
    black_player_id UUID REFERENCES players(id),
    result VARCHAR(10),
    moves TEXT,
    date_played TIMESTAMP,
    time_control VARCHAR(50),
    opening_id UUID REFERENCES openings(id),
    eco_code VARCHAR(10)
);
```

### Analysis
```sql
CREATE TABLE analysis (
    id UUID PRIMARY KEY,
    game_id UUID REFERENCES games(id),
    position_fen VARCHAR(100),
    evaluation FLOAT,
    depth INTEGER,
    best_move VARCHAR(10),
    analysis_time TIMESTAMP
);
```

### Opening
```sql
CREATE TABLE openings (
    id UUID PRIMARY KEY,
    eco_code VARCHAR(10) UNIQUE,
    name VARCHAR(255),
    moves TEXT,
    description TEXT
);
```

## Supporting Models

### Endpoint
- Tracks API endpoint usage
- Monitors performance metrics

### Request
- Logs API requests
- Stores request metadata

## Relationships
- Games link to Players (white/black)
- Games link to Openings
- Analysis links to Games

## Data Access Patterns

### Connection Management
```python
# Database pool configuration
pool = await asyncpg.create_pool(
    dsn,
    min_size=3,      # Minimum connections
    max_size=10,     # Maximum connections
    command_timeout=60
)
```

### Batch Operations
```python
# Player batch insertion
async with conn.transaction():
    await conn.executemany('''
        INSERT INTO players (name)
        VALUES ($1)
        ON CONFLICT (name) DO UPDATE 
        SET name = EXCLUDED.name
        RETURNING id
    ''', player_names)

# Game batch insertion (50 records per batch)
async with conn.transaction(isolation='read_committed'):
    await conn.executemany('''
        INSERT INTO games (
            white_player_id, black_player_id, 
            white_elo, black_elo, 
            date, result, eco, moves
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::bytea)
    ''', game_records)
```

### Query Optimization
```python
# Eager loading relationships
query = (
    select(GameDB)
    .options(
        joinedload(GameDB.white_player),
        joinedload(GameDB.black_player)
    )
    .where(GameDB.id == game_id)
)

# Materialized view for analytics
CREATE MATERIALIZED VIEW game_stats AS
SELECT
    COUNT(*) as total_games,
    COUNT(DISTINCT player_id) as total_players,
    AVG(moves_count) as avg_moves_per_game
FROM games;
```

## Caching Strategy

### Analysis Cache
```python
# Configuration
analysis_ttl = {
    'move_distribution': timedelta(hours=12),
    'opening_analysis': timedelta(hours=6),
    'player_performance': timedelta(hours=4),
    'db_metrics': timedelta(minutes=5)
}

# Usage
async def get_database_metrics():
    cache_key = 'db_metrics'
    if cached := await cache.get(cache_key):
        return cached
    
    metrics = await compute_metrics()
    await cache.set(cache_key, metrics)
    return metrics
```

### Game Cache
```python
# Configuration
game_ttl = {
    'game_': timedelta(minutes=60),   # Individual games
    'games_': timedelta(minutes=15),  # Game lists
    'stats_': timedelta(minutes=30),  # Statistics
    'analysis_': timedelta(minutes=45) # Analysis results
}

# Usage
async def get_game_by_id(game_id: int):
    cache_key = f'game_{game_id}'
    if cached := await cache.get(cache_key):
        return cached
        
    game = await fetch_game(game_id)
    await cache.set(cache_key, game)
    return game
```

### HTTP Caching
```python
# Router configuration
@router.get("/database-metrics")
async def get_metrics(response: Response):
    response.headers["Cache-Control"] = "public, max-age=3600"
    return await get_metrics()

# Global cache settings
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
CACHE_CONTROL_VALUE = f"public, max-age={CACHE_TTL}"
```

### Cache Invalidation
```python
async def invalidate_caches(game_id: int):
    # Invalidate game cache
    await cache.delete(f'game_{game_id}')
    
    # Invalidate related caches
    await cache.delete('recent_games')
    await cache.delete('game_stats')
    
    # Invalidate player caches
    for player_id in [game.white_id, game.black_id]:
        await cache.delete(f'player_{player_id}')
