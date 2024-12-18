"""
Router for player-related endpoints.
Handles player search, statistics, and performance analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

import logging

logger = logging.getLogger(__name__)

from database import get_session
from repository import PlayerRepository, opening_repository
from repository.models import (
    PlayerResponse,
    PlayerSearchResponse,
    PlayerPerformanceResponse,
    DetailedPerformanceResponse,
    OpeningAnalysisResponse
)



router = APIRouter()

@router.get("/search", response_model=List[PlayerSearchResponse])
async def search_players(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=10, gt=0, le=100),
    db: AsyncSession = Depends(get_session)
):
    """
    Search for players by name.
    Returns a list of matching players with basic info.
    """
    try:
        repo = PlayerRepository(db)
        return await repo.search_players(q, limit)
    except Exception as e:
        logger.error(f"Error searching players: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search players")

@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Get detailed information about a specific player.
    """
    repo = PlayerRepository(db)
    player = await repo.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@router.get("/{player_id}/performance", response_model=List[DetailedPerformanceResponse])
async def get_player_performance(
    player_id: int,
    time_period: Optional[str] = None,
    db: AsyncSession = Depends(get_session)
):
    """
    Get performance statistics for a player over time.
    Optional time_period parameter to filter results (e.g., '1y', '6m', '3m', '1m').
    """
    repo = PlayerRepository(db)
    performance = await repo.get_player_performance(player_id, time_period)
    if not performance:
        raise HTTPException(status_code=404, detail="Player not found or no performance data available")
    return performance

@router.get("/{player_id}/detailed-stats", response_model=DetailedPerformanceResponse)
async def get_detailed_stats(
    player_id: int,
    time_period: Optional[str] = None,
    db: AsyncSession = Depends(get_session)
):
    """
    Get detailed performance statistics for a player.
    Includes opening preferences, time management, and rating progression.
    """
    repo = PlayerRepository(db)
    stats = await repo.get_detailed_stats(player_id, time_period)
    if not stats:
        raise HTTPException(status_code=404, detail="Player not found or no statistics available")
    return stats


@router.get("/{player_id}/openings", response_model=OpeningAnalysisResponse)
async def get_player_openings(
    response: Response,
    player_id: str = Path(..., description="The ID of the player to analyze"),
    min_games: int = Query(default=5, ge=1, description="Minimum number of games for opening analysis"),
    limit: Optional[int] = Query(default=None, ge=1, le=100, description="Maximum number of openings to return"),
    start_date: Optional[str] = Query(
        None,
        description="Start date for analysis (YYYY-MM-DD)",
        regex="^\d{4}-\d{2}-\d{2}$"
    ),
    end_date: Optional[str] = Query(
        None,
        description="End date for analysis (YYYY-MM-DD)",
        regex="^\d{4}-\d{2}-\d{2}$"
    ),
    db: AsyncSession = Depends(get_session)
) -> OpeningAnalysisResponse:
    """
    Get detailed analysis of a player's opening performance.
    
    Parameters:
    - player_id: Player's username or ID
    - min_games: Minimum number of games required for an opening to be included (default: 5)
    - limit: Maximum number of openings to return (optional, max 100)
    - start_date: Optional start date for filtering games (YYYY-MM-DD)
    - end_date: Optional end date for filtering games (YYYY-MM-DD)
    
    Returns:
    - Detailed analysis of the player's opening performance including:
        - List of all openings played with stats
        - Overall analysis insights
        - Most successful and most played openings
    """
    try:
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        
        if end_date:
            try:
                parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        # Validate date range
        if parsed_start_date and parsed_end_date and parsed_start_date > parsed_end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date cannot be later than end_date"
            )
        
        # Convert player_id to integer
        try:
            player_id_int = int(player_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="player_id must be an integer")
        
        # Get opening analysis
        analysis = await opening_repository.get_player_openings(
            db=db,
            player_id=player_id_int,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            min_games=min_games,
            limit=limit
        )
        
        # Set cache header (cache for 5 minutes)
        response.headers["Cache-Control"] = "public, max-age=300"
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error getting player opening analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get player opening analysis"
        )
