"""
Router for analysis-related endpoints.
Handles game analysis, statistics, and database metrics.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta, date
import logging

from database import get_session
from repository import PlayerRepository, AnalysisRepository
from repository.models import (
    MoveCountAnalysis,
    PlayerPerformanceResponse,
    OpeningAnalysisResponse,
    DatabaseMetricsResponse,
    PlayerSearchResponse,
    DetailedPerformanceResponse
)
from repository.analysis import AnalysisCacheManager
from config import CACHE_CONTROL_HEADER
from repository.models.opening import PopularOpeningStats
from repository import opening_repository

logger = logging.getLogger(__name__)
router = APIRouter()
cache_manager = AnalysisCacheManager()

@router.get("/move-counts", response_model=List[MoveCountAnalysis])
async def get_move_count_distribution(
    response: Response,
    db: AsyncSession = Depends(get_session)
):
    """Get distribution analysis of move counts across chess games."""
    try:
        repo = AnalysisRepository(db)
        distribution = await repo.get_move_count_distribution()
        # response.headers[CACHE_CONTROL_HEADER] = "max-age=3600"  # Cache for 1 hour
        return distribution
    except Exception as e:
        logger.error(f"Error getting move count distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database-metrics", response_model=DatabaseMetricsResponse)
async def get_database_metrics(
    response: Response,
    db: AsyncSession = Depends(get_session)
):
    """Get comprehensive database metrics and trends."""
    try:
        repo = AnalysisRepository(db)
        metrics = await repo.get_database_metrics()
        response.headers[CACHE_CONTROL_HEADER] = "max-age=3600"  # Cache for 1 hour
        return metrics
    except Exception as e:
        logger.error(f"Error getting database metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/popular-openings", response_model=List[PopularOpeningStats])
async def get_popular_openings(
    response: Response,
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
    min_games: int = Query(default=100, ge=1, description="Minimum number of games for an opening to be included"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of openings to return"),
    db: AsyncSession = Depends(get_session)
) -> List[PopularOpeningStats]:
    """
    Get statistics for popular chess openings.
    
    Parameters:
    - start_date: Optional start date for filtering games (YYYY-MM-DD)
    - end_date: Optional end date for filtering games (YYYY-MM-DD)
    - min_games: Minimum number of games required for an opening to be included (default: 100)
    - limit: Maximum number of openings to return (default: 10, max: 50)
    
    Returns:
    - List of popular openings with their statistics
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
        
        # Get popular openings
        openings = await opening_repository.get_popular_openings(
            db=db,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            min_games=min_games,
            limit=limit
        )
        
        # Set cache header (cache for 5 minutes)
        response.headers["Cache-Control"] = "public, max-age=300"
        
        return openings
        
    except Exception as e:
        logger.error(f"Error getting popular openings: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get popular openings"
        )