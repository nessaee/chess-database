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
