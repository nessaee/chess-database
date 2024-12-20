"""
Router for chess game endpoints.
Handles game queries, statistics, and individual game details.
"""

from fastapi import APIRouter, Depends, Query, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from database import get_session
from repository.game.repository import GameRepository
from repository.models import GameResponse
from repository.common.errors import DatabaseOperationError
from config import CACHE_CONTROL_HEADER, CACHE_CONTROL_VALUE

logger = logging.getLogger(__name__)

router = APIRouter()

# Get game count
@router.get("/count")
async def count_games(
    db: AsyncSession = Depends(get_session)
) -> int:
    """Get total number of games in database."""
    game_repository = GameRepository(db)
    return await game_repository.count_games()

# Get list of games
@router.get("", response_model=List[GameResponse])
async def read_games(
    response: Response,
    player_name: Optional[str] = None,
    player_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    only_dated: bool = False,
    limit: int = Query(default=50, gt=0, le=100),
    move_notation: str = Query(default='uci', regex='^(uci|san)$'),
    db: AsyncSession = Depends(get_session)
) -> List[GameResponse]:
    """
    Get list of chess games with optional filters.
    
    Args:
        player_name: Filter by player name
        start_date: Filter games after this date (YYYY-MM-DD)
        end_date: Filter games before this date (YYYY-MM-DD)
        only_dated: Only include games with valid dates
        limit: Maximum number of games to return
        move_notation: Move notation format ('uci' or 'san')
    """
    try:
        # Validate dates if provided
        if start_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        
        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )

        # Get games from repository
        game_repository = GameRepository(db)
        games = await game_repository.get_games(
            player_name=player_name,
            player_id=player_id,
            start_date=start_date,
            end_date=end_date,
            only_dated=only_dated,
            limit=limit,
            move_notation=move_notation
        )
        
        return games
        
    except DatabaseOperationError as e:
        logger.error(f"Database error in read_games: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in read_games: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Get player name suggestions
@router.get("/players/suggest")
async def suggest_players(
    name: str = Query(..., min_length=1),
    limit: int = Query(default=10, gt=0, le=100),
    db: AsyncSession = Depends(get_session)
) -> List[str]:
    """Get player name suggestions based on partial input."""
    try:
        game_repository = GameRepository(db)
        return await game_repository.suggest_players(name, limit)
    except DatabaseOperationError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get game stats
@router.get("/stats")
async def get_game_stats(
    response: Response,
    db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Get summary statistics for all games."""
    try:
        repository = GameRepository(db)
        stats = await repository.get_game_stats()
        return stats
    except DatabaseOperationError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get player games
@router.get("/player/{player_name}", response_model=List[GameResponse])
async def get_player_games(
    player_name: str,
    response: Response,
    start_date: Optional[str] = Query(None, regex="^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, regex="^\d{4}-\d{2}-\d{2}$"),
    only_dated: bool = Query(False),
    limit: int = Query(default=50, gt=0, le=100),
    move_notation: str = Query(default='uci', regex='^(uci|san)$'),
    db: AsyncSession = Depends(get_session)
) -> List[GameResponse]:
    """
    Get list of chess games for a specific player.
    
    Args:
        player_name: Name of the player to fetch games for
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        only_dated: If true, only return games with dates
        limit: Maximum number of games to return
        move_notation: Move notation format ('uci' or 'san')
        
    Returns:
        List of games matching the criteria
    """
    try:
        game_repository = GameRepository(db)
        games = await game_repository.get_player_games(
            player_name=player_name,
            start_date=start_date,
            end_date=end_date,
            only_dated=only_dated,
            limit=limit,
            move_notation=move_notation
        )
        response.headers[CACHE_CONTROL_HEADER] = CACHE_CONTROL_VALUE
        return games
    except DatabaseOperationError as e:
        logger.error(f"Database error fetching games for player {player_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching games for player {player_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch player games")

# Get recent games
@router.get("/recent", response_model=List[GameResponse])
async def get_recent_games(
    response: Response,
    limit: int = Query(default=10, gt=0, le=50),
    move_notation: str = Query(default='uci', regex='^(uci|san)$'),
    db: AsyncSession = Depends(get_session)
) -> List[GameResponse]:
    """
    Get most recent chess games.
    
    Args:
        limit: Maximum number of games to return (default: 10, max: 50)
        move_notation: Move notation format ('uci' or 'san')
    
    Returns:
        List of most recent games
    """
    try:
        game_repository = GameRepository(db)
        games = await game_repository.get_recent_games(limit)
        response.headers[CACHE_CONTROL_HEADER] = CACHE_CONTROL_VALUE
        return games
    except Exception as e:
        logger.error(f"Error fetching recent games: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recent games")

# Get game by ID - Keep this last to avoid route conflicts
@router.get("/{game_id}", response_model=GameResponse)
async def read_game(
    game_id: int,
    response: Response,
    move_notation: str = Query(default='uci', regex='^(uci|san)$'),
    db: AsyncSession = Depends(get_session)
) -> GameResponse:
    """
    Get a specific game by ID.
    
    Args:
        game_id: ID of the game to retrieve
        move_notation: Move notation format ('uci' or 'san')
    """
    try:
        repository = GameRepository(db)
        game = await repository.get_game_by_id(game_id, move_notation=move_notation)
        
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
            
        return game
        
    except DatabaseOperationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
