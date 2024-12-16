# Chess Database Repository

A comprehensive repository layer for managing chess game data, analysis, and related metadata.

## Structure

```
repository/
├── models/          # Database models and response types
├── game/           # Game-related operations
├── player/         # Player management
├── analysis/       # Game analysis and metrics
├── common/         # Shared utilities
└── item/           # Item management
```

## Dependencies

Core dependencies:
- SQLAlchemy (>=2.0.0): Database ORM
- FastAPI (>=0.100.0): Web framework
- Pydantic (>=2.0.0): Data validation
- python-chess (>=1.9.0): Chess move validation

Database:
- asyncpg (>=0.28.0): PostgreSQL async driver

Utilities:
- python-dateutil (>=2.8.2): Date parsing
- tenacity (>=8.2.0): Retry logic
- structlog (>=23.1.0): Structured logging

## Models

The repository uses both SQLAlchemy models for database operations and Pydantic models for API responses:

- Database Models:
  - GameDB: Chess game records
  - PlayerDB: Player information
  - ItemDB: Generic items
  
- Response Models:
  - GameResponse: Game data with player info
  - PlayerResponse: Basic player info
  - PlayerSearchResponse: Search results
  - PlayerPerformanceResponse: Performance metrics
  - DetailedPerformanceResponse: Detailed stats
  - OpeningAnalysisResponse: Opening analysis

## Usage

```python
from repository import GameRepository, PlayerRepository
from sqlalchemy.ext.asyncio import AsyncSession

# Initialize repositories
game_repo = GameRepository(db_session)
player_repo = PlayerRepository(db_session)

# Search for players
players = await player_repo.search_players("Magnus")

# Get games with filters
games = await game_repo.get_games(
    player_name="Carlsen",
    start_date="2024-01-01"
)
```

## Error Handling

The repository implements consistent error handling:
- ValidationError: For invalid input data
- DatabaseError: For database operation failures
- HTTPException: For API-level errors

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Maintain type hints and docstrings
