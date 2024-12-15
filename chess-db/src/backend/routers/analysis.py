# routers/analysis.py
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from database import get_db
from models import (
    MoveCountAnalysis,
    PlayerPerformanceResponse,
    OpeningAnalysisResponse,
    DatabaseMetricsResponse,
    PlayerSearchResponse,
    DetailedPerformanceResponse
)
from repository import AnalysisRepository
from config import CACHE_CONTROL_HEADER


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/move-counts", response_model=List[MoveCountAnalysis])
async def get_move_count_distribution(
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Get distribution analysis of move counts across chess games."""
    try:
        repo = AnalysisRepository(db)
        results = await repo.get_move_count_distribution()
        response.headers["Cache-Control"] = CACHE_CONTROL_HEADER
        return results
    except Exception as e:
        logger.error(f"Error analyzing move counts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze move counts")

@router.get("/database/metrics", response_model=DatabaseMetricsResponse)
async def get_database_metrics(
    time_period: str = Query("1m", description="Time period (1m, 3m, 6m, 1y)"),
    db: AsyncSession = Depends(get_db)
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
        start_date = end_date - period_map.get(time_period, timedelta(days=30))
        
        stats = await repo.get_database_metrics(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
        if not stats:
            raise HTTPException(status_code=404, detail="No database metrics available")
            
        return stats
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving database metrics: {str(e)}")

@router.get(
    "/players/{player_id}/opening-analysis",
    response_model=OpeningAnalysisResponse,
    tags=["Analysis"],
    summary="Analyze player's opening performance"
)
async def get_player_opening_analysis(
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
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed analysis of a player's performance with different chess openings.
    Includes statistics such as win rates, game counts, and average game lengths.
    """
    try:
        repository = AnalysisRepository(db)
        analysis = await repository.get_player_opening_analysis(
            player_id=player_id,
            min_games=min_games,
            start_date=start_date,
            end_date=end_date
        )
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"No opening analysis found for player {player_id}"
            )
            
        return analysis
        
    except ValueError as e:
        logger.error(f"Validation error in opening analysis: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in opening analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze opening performance"
        )

@router.get(
    "/players/{player_id}/performance",
    response_model=List[PlayerPerformanceResponse]
)
async def get_player_performance(
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
    db: AsyncSession = Depends(get_db)
):
    """Get detailed performance metrics for a player over time."""
    try:
        repository = AnalysisRepository(db)
        performance = await repository.get_player_performance_timeline(
            player_id=player_id,
            time_range=time_range,
            start_date=start_date,
            end_date=end_date
        )
        
        if not performance:
            raise HTTPException(
                status_code=404,
                detail=f"No performance data found for player {player_id}"
            )
        
        return performance
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in performance analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze player performance"
        )



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
    db: AsyncSession = Depends(get_db)
):
    """
    Search for players by partial name match.
    Results are ordered by relevance and include recent ELO ratings if available.
    """
    try:
        if not query:
            return []

        repository = AnalysisRepository(db)
        results = await repository.search_players(
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
