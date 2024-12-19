# Data Models Design

## Core Models

### Game Model

#### Schema
```python
class GameDB(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    white_player_id = Column(Integer, ForeignKey("players.id"))
    black_player_id = Column(Integer, ForeignKey("players.id"))
    white_elo = Column(SmallInteger, nullable=True)
    black_elo = Column(SmallInteger, nullable=True)
    date = Column(Date)
    result = Column(SmallInteger)  # 2-bit result encoding
    eco = Column(String(3))
```

#### Result Encoding
```python
RESULT_UNKNOWN = 0  # '*'
RESULT_DRAW = 1     # '1/2-1/2'
RESULT_WHITE = 2    # '1-0'
RESULT_BLACK = 3    # '0-1'
```

#### Response Model
```python
class GameResponse(BaseModel):
    id: int
    white_player_id: int
    black_player_id: int
    white_player: Optional[PlayerInGame]
    black_player: Optional[PlayerInGame]
    date: Optional[date]
    result: str
    eco: Optional[str]
    moves: Optional[List[str]]
    moves_san: Optional[List[str]]
    num_moves: Optional[int]
    opening_name: Optional[str]
```

### Player Model

#### Schema
```python
class PlayerDB(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
```

#### Response Models
```python
class PlayerResponse(BaseModel):
    id: int
    name: str

class PlayerSearchResponse(BaseModel):
    id: int
    name: str
    elo: Optional[int]

class PlayerPerformanceResponse(BaseModel):
    games_played: int
    wins: int
    losses: int
    draws: int
    win_rate: float
    avg_elo: Optional[int]
```

### Analysis Models

#### Performance Analysis
```python
class PlayerPerformanceResponse(BaseModel):
    time_period: str
    games_played: int
    wins: int
    losses: int
    draws: int
    win_rate: float
    avg_moves: float
    white_games: int
    black_games: int
    elo_rating: Optional[int]
```

#### Opening Analysis
```python
class OpeningAnalysisResponse(BaseModel):
    analysis: List[OpeningAnalysis]
    total_openings: int
    avg_game_length: float
    total_games: int
    total_wins: int
    total_draws: int
    total_losses: int
    most_successful: str
    most_played: str
```

#### Detailed Performance
```python
class DetailedPerformanceResponse(BaseModel):
    player_id: int
    total_games: int
    win_rate: float
    draw_rate: float
    loss_rate: float
    opening_diversity: float
    favorite_opening: str
    opening_win_rate: float
    avg_game_length: float
    time_control_preference: str
    piece_placement_accuracy: float
    tactical_accuracy: float
    recent_performance_trend: float
    last_updated: datetime
```

## Monitoring Models

### Endpoint Metrics
```python
class EndpointMetrics(BaseModel):
    endpoint: str
    method: str
    total_calls: int
    successful_calls: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    max_response_time: float
    min_response_time: float
    error_count: int
    success_rate: float
    error_rate: float
    avg_response_size: float
    max_response_size: int
    min_response_size: int
```

### Database Metrics
```python
class DatabaseMetricsResponse(BaseModel):
    total_games: int
    total_players: int
    avg_moves_per_game: float
    avg_game_duration: float
    performance: Dict[str, float]
    growth_trends: Dict[str, float]
    health_metrics: Dict[str, float]
    endpoint_metrics: List[EndpointMetrics]
```

## Data Validation

### Game Validation
- Valid player IDs
- Valid ELO ratings (0-3000)
- Valid ECO codes (3 characters)
- Valid result encoding (0-3)

### Player Validation
- Unique player names
- Valid ELO ratings
- Non-negative game counts
- Performance metric consistency

### Analysis Validation
- Valid move counts (0-500)
- Valid time periods
- Consistent game counts
- Valid statistical ranges

## Model Relationships

### Direct Relationships
1. Game -> Players (Many-to-Two)
   - White player
   - Black player
2. Game -> Opening (Many-to-One)
3. Performance -> Player (Many-to-One)

### Derived Data
1. Player Statistics
   - Aggregated from games
   - Performance metrics
   - Opening preferences
2. Opening Statistics
   - Usage frequency
   - Success rates
   - Player preferences
