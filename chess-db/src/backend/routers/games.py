# routers/games.py
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from database import get_db
from models import GameResponse
from repository import GameRepository
from config import CACHE_CONTROL_HEADER

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("", response_model=List[GameResponse])
async def read_games(
    response: Response,
    player_name: Optional[str] = None,
    start_date: Optional[str] = Query(None, regex="^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, regex="^\d{4}-\d{2}-\d{2}$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get games with filtering and pagination."""
    try:
        repo = GameRepository(db)
        games = await repo.get_games(
            player_name=player_name,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        response.headers["Cache-Control"] = CACHE_CONTROL_HEADER
        return games
    except Exception as e:
        logger.error(f"Error fetching games: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch games")

@router.get("/{game_id}", response_model=GameResponse)
async def read_game(
    game_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific game by ID."""
    try:
        repo = GameRepository(db)
        game = await repo.get_game(game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        return game
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching game {game_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch game")

@router.get("/stats/summary")
async def get_game_stats(
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Get summary statistics for all games."""
    try:
        repo = GameRepository(db)
        stats = await repo.get_game_stats()
        response.headers["Cache-Control"] = CACHE_CONTROL_HEADER
        return stats
    except Exception as e:
        logger.error(f"Error fetching game stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch game statistics")




