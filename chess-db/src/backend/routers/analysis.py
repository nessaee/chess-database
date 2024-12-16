"""
Router for analysis-related endpoints.
Handles game analysis, statistics, and database metrics.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from database import get_session
from repository.models import (
    MoveCountAnalysis,
    PlayerPerformanceResponse,
    OpeningAnalysisResponse,
    DatabaseMetricsResponse,
    PlayerSearchResponse,
    DetailedPerformanceResponse
)
from repository.analysis import AnalysisRepository, AnalysisCacheManager
from config import CACHE_CONTROL_HEADER

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])
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

@router.get("/database/metrics", response_model=DatabaseMetricsResponse)
async def get_database_metrics(
    response: Response,
    time_period: str = Query("1m", description="Time period (1m, 3m, 6m, 1y)"),
    db: AsyncSession = Depends(get_session)
):
    """Get comprehensive database metrics and trends."""
    try:
        repo = AnalysisRepository(db)
        end_date = datetime.now()
        period_map = {
            "1m": timedelta(days=30),
            "3m": timedelta(days=90),
            "6m": timedelta(days=180),
            "1y": timedelta(days=365)
        }
        
        if time_period not in period_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid time period. Must be one of: {', '.join(period_map.keys())}"
            )
            
        start_date = end_date - period_map[time_period]
        
        stats = await repo.get_database_metrics(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        if not stats:
            raise HTTPException(status_code=404, detail="No database metrics available")
            
        response.headers[CACHE_CONTROL_HEADER] = "max-age=1800"  # Cache for 30 minutes
        return stats
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting database metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get(
    "/players/{player_id}/openings",
    response_model=OpeningAnalysisResponse
)
async def get_player_opening_analysis(
    response: Response,
    player_id: int = Path(..., description="The ID of the player to analyze", ge=1),
    min_games: int = Query(5, ge=1, description="Minimum games threshold"),
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
):
    """
    Get detailed analysis of a player's performance with different chess openings.
    Includes statistics such as win rates, game counts, and average game lengths.
    """
    try:
        # Validate dates if provided
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date cannot be later than end_date"
            )

        repo = AnalysisRepository(db)
        analysis = await repo.get_player_opening_analysis(
            player_id=player_id,
            min_games=min_games,
            start_date=start_date,
            end_date=end_date
        )
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"No opening analysis available for player {player_id}"
            )
            
        response.headers[CACHE_CONTROL_HEADER] = "max-age=3600"  # Cache for 1 hour
        return analysis
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing player openings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get(
    "/players/{player_id}/performance",
    response_model=DetailedPerformanceResponse
)
async def get_player_performance(
    response: Response,
    player_id: int = Path(..., description="ID of the player to analyze", ge=1),
    time_range: str = Query(
        "monthly",
        description="Time grouping (daily, weekly, monthly, yearly)"
    ),
    start_date: Optional[str] = Query(
        None,
        description="Start date (YYYY-MM-DD)",
        regex="^\d{4}-\d{2}-\d{2}$"
    ),
    end_date: Optional[str] = Query(
        None,
        description="End date (YYYY-MM-DD)",
        regex="^\d{4}-\d{2}-\d{2}$"
    ),
    db: AsyncSession = Depends(get_session)
):
    """Get detailed performance metrics for a player over time."""
    try:
        valid_ranges = ["daily", "weekly", "monthly", "yearly"]
        if time_range not in valid_ranges:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid time_range. Must be one of: {', '.join(valid_ranges)}"
            )

        # Validate dates if provided
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date cannot be later than end_date"
            )

        repo = AnalysisRepository(db)
        performance = await repo.get_player_performance(
            player_id=player_id,
            time_range=time_range,
            start_date=start_date,
            end_date=end_date
        )
        
        if not performance:
            raise HTTPException(
                status_code=404,
                detail=f"No performance data available for player {player_id}"
            )
            
        response.headers[CACHE_CONTROL_HEADER] = "max-age=1800"  # Cache for 30 minutes
        return performance
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting player performance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/players/search", response_model=List[PlayerSearchResponse], include_in_schema=True)
async def search_players(
    query: str = Query(
        None,
        alias="q",
        min_length=2,
        max_length=50,
        description="Search query for player name"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Maximum number of results to return"
    ),
    db: AsyncSession = Depends(get_session)
):
    """
    Search for players by partial name match.
    Results are ordered by relevance and include recent ELO ratings if available.
    """
    try:
        if not query:
            return []

        repo = AnalysisRepository(db)
        results = await repo.search_players(
            query=query.strip(),
            limit=limit
        )

        return [
            PlayerSearchResponse(
                id=result["id"],
                name=result["name"],
                elo=result.get("elo")
            )
            for result in results
        ]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Player search error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search players")
