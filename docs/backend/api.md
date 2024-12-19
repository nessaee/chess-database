# API Design Specification

[← Documentation Home](../../index.md) | [Design Overview](../README.md) | [System Diagram](../system-diagram.md)

**Path**: documentation/design/backend/api.md

## Navigation
- [Overview](#overview)
- [API Structure](#api-structure)
  - [Game Operations](#game-operations)
  - [Player Operations](#player-operations)
  - [Analysis Operations](#analysis-operations)
  - [Database Operations](#database-operations)
- [Request/Response Models](#requestresponse-models)
- [Error Handling](#error-handling)
- [API Security](#api-security)
- [Performance Optimization](#performance-optimization)

## Overview

The Chess Database backend is built using FastAPI, providing a modern, fast, and type-safe API for chess game analysis and player statistics. All endpoints are documented using OpenAPI/Swagger and are accessible through `/docs` or `/redoc`.

## API Structure

### Game Operations

#### Endpoints

##### GET /api/games
```python
@router.get("/games")
async def list_games(
    limit: int = 10,
    offset: int = 0,
    player: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> List[Game]:
    """Retrieve a list of games with filtering options"""
```

##### POST /api/games
```python
@router.post("/games")
async def create_game(
    game: GameCreate
) -> Game:
    """Create a new game record"""
```

##### GET /api/games/{game_id}
```python
@router.get("/games/{game_id}")
async def get_game(
    game_id: UUID
) -> Game:
    """Retrieve a specific game by ID"""
```

##### PUT /api/games/{game_id}
```python
@router.put("/games/{game_id}")
async def update_game(
    game_id: UUID,
    game: GameUpdate
) -> Game:
    """Update game information"""
```

##### DELETE /api/games/{game_id}
```python
@router.delete("/games/{game_id}")
async def delete_game(
    game_id: UUID
) -> None:
    """Remove a game from the database"""
```

### Player Operations

#### Endpoints

##### GET /api/players
```python
@router.get("/players")
async def list_players(
    limit: int = 10,
    offset: int = 0,
    rating_min: Optional[int] = None,
    rating_max: Optional[int] = None
) -> List[Player]:
    """Retrieve a list of players with filtering options"""
```

##### POST /api/players
```python
@router.post("/players")
async def create_player(
    player: PlayerCreate
) -> Player:
    """Create a new player profile"""
```

##### GET /api/players/{player_id}
```python
@router.get("/players/{player_id}")
async def get_player(
    player_id: UUID
) -> Player:
    """Retrieve a specific player by ID"""
```

##### PUT /api/players/{player_id}
```python
@router.put("/players/{player_id}")
async def update_player(
    player_id: UUID,
    player: PlayerUpdate
) -> Player:
    """Update player information"""
```

##### DELETE /api/players/{player_id}
```python
@router.delete("/players/{player_id}")
async def delete_player(
    player_id: UUID
) -> None:
    """Remove a player profile"""
```

### Analysis Operations

#### Endpoints

##### POST /api/analysis/position
```python
@router.post("/analysis/position")
async def analyze_position(
    fen: str,
    depth: int = 20
) -> PositionAnalysis:
    """Analyze a specific position"""
```

##### POST /api/analysis/game/{game_id}
```python
@router.post("/analysis/game/{game_id}")
async def analyze_game(
    game_id: UUID,
    depth: int = 20
) -> GameAnalysis:
    """Analyze an entire game"""
```

##### GET /api/analysis/game/{game_id}
```python
@router.get("/analysis/game/{game_id}")
async def get_game_analysis(
    game_id: UUID
) -> GameAnalysis:
    """Get existing analysis for a game"""
```

### Database Operations

#### Endpoints

##### GET /api/database/health
```python
@router.get("/database/health")
async def check_health() -> HealthStatus:
    """Check database health status"""
```

##### POST /api/database/backup
```python
@router.post("/database/backup")
async def backup_database() -> None:
    """Trigger database backup"""
```

##### GET /api/database/stats
```python
@router.get("/database/stats")
async def get_stats() -> DatabaseStats:
    """Get database statistics"""
```

## Request/Response Models

### Game Models
```python
class GameCreate(BaseModel):
    white_player_id: UUID
    black_player_id: UUID
    moves: str
    result: str
    time_control: str

class Game(GameCreate):
    id: UUID
    date_played: datetime
    opening_id: Optional[UUID]
    eco_code: Optional[str]
```

### Player Models
```python
class PlayerCreate(BaseModel):
    username: str
    rating: int

class Player(PlayerCreate):
    id: UUID
    join_date: datetime
    last_active: datetime
    total_games: int
    wins: int
    losses: int
    draws: int
```

### Analysis Models
```python
class PositionAnalysis(BaseModel):
    fen: str
    evaluation: float
    depth: int
    best_move: str
    pv: List[str]

class GameAnalysis(BaseModel):
    game_id: UUID
    positions: List[PositionAnalysis]
    summary: Dict[str, Any]
```

## Error Handling

### Error Responses
```python
class ErrorResponse(BaseModel):
    code: int
    message: str
    details: Optional[Dict[str, Any]]
```

### HTTP Status Codes
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

## API Security

### Authentication
- JWT Token-based
- API Key validation
- Session management

### Authorization
- Role-based access
- Resource ownership
- Permission levels

### Rate Limiting
- Request quotas
- Throttling rules
- Burst allowance

## Performance Optimization

### Caching
- Response caching
- Query caching
- Cache invalidation

### Pagination
- Cursor-based
- Offset-based
- Result limiting

### Query Optimization
- Eager loading
- Selective fields
- Indexed queries
