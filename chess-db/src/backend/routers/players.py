"""
Router for player-related endpoints.
Handles player search, statistics, and performance analysis.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from repository import PlayerRepository
from repository.models import (
    PlayerResponse,
    PlayerSearchResponse,
    PlayerPerformanceResponse,
    DetailedPerformanceResponse
)

router = APIRouter(
    prefix="/players",
    tags=["players"]
)
@router.get("", response_model=List[PlayerSearchResponse])
async def search_players(
    name: Optional[str] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_session)
):
    """
    Search for players by name.
    Returns a list of matching players with basic info.
    """
    repo = PlayerRepository(db)
    return await repo.search_players(name, limit) if name else await repo.get_players(limit)

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

@router.get("/{player_id}/performance", response_model=List[PlayerPerformanceResponse])
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
