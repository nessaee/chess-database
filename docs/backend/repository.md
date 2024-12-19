# Repository Layer Design

[← Documentation Home](../../index.md) | [Design Overview](../README.md) | [API Reference](api.md)

**Path**: documentation/design/backend/repository.md

## Navigation
- [Overview](#overview)
- [Domain Repositories](#domain-repositories)
  - [Game Repository](#game-repository)
  - [Player Repository](#player-repository)
  - [Analysis Repository](#analysis-repository)
  - [Opening Repository](#opening-repository)
- [Common Components](#common-components)
- [Implementation Details](#implementation-details)
- [Error Handling](#error-handling)

## Overview

The repository layer implements data access patterns and business logic using SQLAlchemy. Each domain has its own repository with specialized operations.

## Domain Repositories

### Game Repository

Handles chess game storage and retrieval:

```python
class GameRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(session)
        self.model = Game

    async def create_from_pgn(self, pgn: str) -> Game:
        """Create game from PGN format"""
        game_data = self._parse_pgn(pgn)
        return await self.create(game_data)

    async def get_with_analysis(self, id: UUID) -> Optional[Game]:
        """Get game with analysis data"""
        query = (
            select(Game)
            .options(joinedload(Game.analysis))
            .where(Game.id == id)
        )
        return await self.session.execute(query)

    async def list_by_player(
        self,
        player_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Game]:
        """Get games by player"""
        query = (
            select(Game)
            .where(or_(
                Game.white_id == player_id,
                Game.black_id == player_id
            ))
            .offset(skip)
            .limit(limit)
        )
        return await self.session.execute(query)
```

### Player Repository

Manages player data and statistics:

```python
class PlayerRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(session)
        self.model = Player

    async def get_statistics(self, id: UUID) -> Dict:
        """Calculate player statistics"""
        stats = await self._calculate_stats(id)
        return stats

    async def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Player]:
        """Search players by name"""
        query = (
            select(Player)
            .where(Player.name.ilike(f"%{query}%"))
            .offset(skip)
            .limit(limit)
        )
        return await self.session.execute(query)

    async def update_rating(
        self,
        id: UUID,
        new_rating: int
    ) -> Optional[Player]:
        """Update player rating"""
        return await self.update(id, {"rating": new_rating})
```

### Analysis Repository

Handles game analysis and position evaluation:

```python
class AnalysisRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(session)
        self.model = GameAnalysis

    async def create_game_analysis(
        self,
        game_id: UUID,
        analysis_data: Dict
    ) -> GameAnalysis:
        """Create analysis for a game"""
        analysis = await self.create({
            "game_id": game_id,
            **analysis_data
        })
        return analysis

    async def get_critical_positions(
        self,
        game_id: UUID
    ) -> List[Dict]:
        """Get critical positions from analysis"""
        analysis = await self.get_by_game_id(game_id)
        return analysis.critical_positions if analysis else []

    async def store_position_evaluation(
        self,
        fen: str,
        evaluation: float,
        best_moves: List[str],
        depth: int
    ) -> PositionAnalysis:
        """Store position analysis"""
        position = PositionAnalysis(
            fen=fen,
            evaluation=evaluation,
            best_moves=best_moves,
            depth=depth
        )
        self.session.add(position)
        await self.session.commit()
        return position
```

### Opening Repository

Manages opening theory and classification:

```python
class OpeningRepository(BaseRepository):
    def __init__(self, session: Session):
        super().__init__(session)
        self.model = Opening

    async def find_by_moves(
        self,
        moves: List[str]
    ) -> Optional[Opening]:
        """Find opening by move sequence"""
        query = (
            select(Opening)
            .where(Opening.moves["moves"].contains(moves))
        )
        return await self.session.execute(query)

    async def get_variations(
        self,
        eco: str
    ) -> List[Dict]:
        """Get opening variations"""
        opening = await self.get_by_eco(eco)
        return opening.variations if opening else []
```

## Common Components

### Error Handling
- Custom exception classes
- Error categorization
- Recovery strategies
- Error logging

### Validation
- Input validation
- Business rule validation
- Data consistency checks
- Constraint enforcement

### Data Transformation
- DTO mapping
- Data normalization
- Format conversion
- Type conversion

### Utilities
- Database helpers
- Query builders
- Cache helpers
- Logging utilities

## Implementation Details

### Query Building
1. Base query construction
2. Filter application
3. Pagination
4. Sorting

### Caching Strategy
1. Cache keys
2. Invalidation rules
3. Cache layers

### Transaction Management
1. Unit of work
2. Rollback handling
3. Consistency checks

## Error Handling

### Error Types
1. Not Found
2. Validation
3. Integrity
4. System

### Error Recovery
1. Retry logic
2. Fallback strategies
3. Error reporting

## Related Documentation
- [API Documentation](api.md)
- [Data Models](models.md)
- [System Architecture](../system-diagram.md)
