# Data Models

[← Documentation Home](../../index.md) | [Design Overview](../README.md) | [API Reference](api.md)

**Path**: documentation/design/backend/models.md

## Navigation
- [Overview](#overview)
- [Core Models](#core-models)
  - [Game Model](#game-model)
  - [Player Model](#player-model)
  - [Analysis Models](#analysis-models)
- [Supporting Models](#supporting-models)
- [Relationships](#relationships)
- [Validation Rules](#validation-rules)

## Overview

The Chess Database uses SQLAlchemy for object-relational mapping with PostgreSQL. Models are organized into distinct domains: Game, Player, Analysis, and Opening.

## Core Models

### Game Model
#### Schema
```python
class GameDB(Base):
    __tablename__ = "games"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    white_id = Column(UUID, ForeignKey("players.id"))
    black_id = Column(UUID, ForeignKey("players.id"))
    result = Column(String)
    moves = Column(JSONB)
    metadata = Column(JSONB)
    
    # Relationships
    white = relationship("Player", foreign_keys=[white_id])
    black = relationship("Player", foreign_keys=[black_id])
    analysis = relationship("GameAnalysis", back_populates="game")
```

#### Response Model
```python
class GameResponse(BaseModel):
    id: UUID
    white_id: UUID
    black_id: UUID
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
    
    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    rating = Column(Integer)
    title = Column(String)
    federation = Column(String)
    metadata = Column(JSONB)
    
    # Relationships
    white_games = relationship("Game", foreign_keys=[Game.white_id])
    black_games = relationship("Game", foreign_keys=[Game.black_id])
```

#### Response Models
```python
class PlayerResponse(BaseModel):
    id: UUID
    name: str

class PlayerSearchResponse(BaseModel):
    id: UUID
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
    player_id: UUID
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

## Supporting Models

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

## Relationships

### Direct Relationships
1. Game → Players (Many-to-Two)
   - White player
   - Black player
2. Game → Opening (Many-to-One)
3. Performance → Player (Many-to-One)

### Derived Data
1. Player Statistics
   - Aggregated from games
   - Performance metrics
   - Opening preferences
2. Opening Statistics
   - Usage frequency
   - Success rates
   - Player preferences

## Validation Rules

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
