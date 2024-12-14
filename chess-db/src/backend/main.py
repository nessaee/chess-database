from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal, init_db
from repository import ItemRepository, GameRepository
from models import ItemCreate, ItemUpdate, ItemResponse, GameResponse
import logging
from repository import AnalysisRepository
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Union, Optional
import logging
import sys
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import HTTPException, Response
from typing import List, Dict, Optional
from pydantic import BaseModel

import logging
# Configure logging with detailed formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('api.log')
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Chess Analysis API",
    description="API for chess game analysis and statistics",
    version="1.0.0"
)

# Configure CORS middleware with explicit settings
app.add_middleware(
    CORSMiddleware,
    # Allow both development and production origins
    allow_origins=[
        "http://localhost:5173",  # Vite development server
        "http://localhost:3000",  # Alternative development port
        "http://frontend:5173",   # Docker service name
    ],
    allow_credentials=True,
    allow_methods=["*"],          # Allow all standard HTTP methods
    allow_headers=["*"],          # Allow all standard HTTP headers
    expose_headers=["*"],         # Expose all response headers
    max_age=3600,                # Cache preflight requests for 1 hour
)

# Database session dependency
async def get_db() -> AsyncSession:
    """
    Provides a database session for route handlers.
    Ensures proper session cleanup after request completion.
    
    Returns:
        AsyncSession: Active database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

# Error handling for database operations
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    Logs the error and returns a structured error response.
    
    Args:
        request: The incoming request
        exc: The raised exception
        
    Returns:
        JSONResponse: Structured error response
    """
    error_id = datetime.utcnow().isoformat()
    logger.error(f"Error ID: {error_id}", exc_info=exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_id": error_id,
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.on_event("startup")
async def startup():
    await init_db()

# Item endpoints
@app.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_db)):
    repo = ItemRepository(db)
    return await repo.create_item(item)

@app.get("/items", response_model=list[ItemResponse])
async def read_items(db: AsyncSession = Depends(get_db)):
    repo = ItemRepository(db)
    return await repo.get_items()

@app.get("/items/{item_id}", response_model=ItemResponse)
async def read_item(item_id: int, db: AsyncSession = Depends(get_db)):
    repo = ItemRepository(db)
    item = await repo.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item: ItemUpdate, db: AsyncSession = Depends(get_db)):
    repo = ItemRepository(db)
    updated_item = await repo.update_item(item_id, item)
    if updated_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item

@app.delete("/items/{item_id}")
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    repo = ItemRepository(db)
    success = await repo.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ok": True}

# Chess game endpoints
@app.get("/games", response_model=list[GameResponse])
async def read_games(
    player_name: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Received request with player_name: {player_name}")
    repo = GameRepository(db)
    games = await repo.get_games(
        player_name=player_name,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    logger.info(f"Found {len(games)} games matching criteria")
    return games

@app.get("/games/{game_id}", response_model=GameResponse)
async def read_game(game_id: int, db: AsyncSession = Depends(get_db)):
    repo = GameRepository(db)
    game = await repo.get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

@app.get("/players/{player_id}/games", response_model=list[GameResponse])
async def read_player_games(player_id: int, db: AsyncSession = Depends(get_db)):
    repo = GameRepository(db)
    games = await repo.get_player_games(player_id)
    if not games:
        raise HTTPException(status_code=404, detail="No games found for this player")
    return games

@app.get("/stats/games")
async def get_game_stats(db: AsyncSession = Depends(get_db)):
    repo = GameRepository(db)
    stats = await repo.get_game_stats()
    return stats



# Data model for move count analysis response
class MoveCountAnalysis(BaseModel):
    """
    Structured response model for move count distribution analysis
    """
    actual_full_moves: int
    number_of_games: int
    avg_bytes: float
    results: str
    min_stored_count: Optional[int]
    max_stored_count: Optional[int]
    avg_stored_count: float

@app.get(
    "/analysis/move-counts",
    response_model=List[MoveCountAnalysis],
    responses={
        200: {"description": "Successfully retrieved move count distribution"},
        500: {"description": "Internal server error during analysis"},
        503: {"description": "Database unavailable"}
    }
)
async def get_move_count_distribution(
    response: Response,
    db: AsyncSession = Depends(get_db)
) -> List[MoveCountAnalysis]:
    """
    Analyze and retrieve the distribution of move counts across all games.
    
    Args:
        response: FastAPI Response object for header manipulation
        db: Database session injected by dependency
        
    Returns:
        List[MoveCountAnalysis]: Statistical analysis of game move counts
        
    Raises:
        HTTPException: On database errors or analysis failures
    """
    try:
        # Initialize analysis repository
        repo = AnalysisRepository(db)
        
        # Retrieve and validate analysis results
        results = await repo.get_move_count_distribution()
        
        # Set cache control headers for optimization
        response.headers["Cache-Control"] = "public, max-age=300"  # Cache for 5 minutes
        
        if not results:
            logger.warning("No game data available for analysis")
            return []
            
        return results
        
    except Exception as e:
        error_id = datetime.utcnow().isoformat()
        logger.error(f"Error ID {error_id}: Failed to analyze move counts", exc_info=e)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to analyze move counts",
                "error_id": error_id,
                "message": str(e)
            }
        )

@app.get("/health")
async def health_check():
    """
    Health check endpoint for Docker container health monitoring.
    Returns basic service health information.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "chess-backend"
    }



# Import additional required Pydantic models
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PlayerPerformanceResponse(BaseModel):
    """Response model for player performance timeline data"""
    time_period: str = Field(..., description="Time period (month/year)")
    games_played: int = Field(..., ge=0, description="Total games played")
    wins: int = Field(..., ge=0, description="Number of wins")
    losses: int = Field(..., ge=0, description="Number of losses")
    draws: int = Field(..., ge=0, description="Number of draws")
    win_rate: float = Field(..., ge=0, le=100, description="Win percentage")
    avg_moves: float = Field(..., ge=0, description="Average moves per game")
    white_games: int = Field(..., ge=0, description="Games played as white")
    black_games: int = Field(..., ge=0, description="Games played as black")
    elo_rating: Optional[int] = Field(None, ge=0, le=3000, description="ELO rating if available")

class OpeningStatsResponse(BaseModel):
    """Response model for opening statistics"""
    eco_code: str = Field(..., description="ECO code of the opening")
    opening_name: str = Field(..., description="Name of the opening")
    games_played: int = Field(..., ge=0, description="Number of games with this opening")
    win_rate: float = Field(..., ge=0, le=100, description="Win rate with this opening")
    avg_moves: float = Field(..., ge=0, description="Average game length with this opening")

@app.get(
    "/players/{player_id}/performance",
    response_model=List[PlayerPerformanceResponse],
    responses={
        200: {"description": "Successfully retrieved player performance data"},
        404: {"description": "Player not found"},
        500: {"description": "Internal server error during analysis"}
    }
)
async def get_player_performance(
    player_id: int,
    time_range: str = 'monthly',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    response: Response = None,
    db: AsyncSession = Depends(get_db)
) -> List[PlayerPerformanceResponse]:
    """
    Get a player's performance statistics over time.
    
    Args:
        player_id: Database ID of the player
        time_range: Aggregation period ('monthly' or 'yearly')
        start_date: Optional start date for analysis (YYYY-MM-DD)
        end_date: Optional end date for analysis (YYYY-MM-DD)
        response: FastAPI Response object for header manipulation
        db: Database session
        
    Returns:
        List[PlayerPerformanceResponse]: Performance statistics over time
        
    Raises:
        HTTPException: If player is not found or analysis fails
    """
    try:
        # Validate time range parameter
        if time_range not in ('monthly', 'yearly'):
            raise HTTPException(
                status_code=400,
                detail="time_range must be 'monthly' or 'yearly'"
            )

        # Validate date format if provided
        for date_str in (start_date, end_date):
            if date_str:
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Dates must be in YYYY-MM-DD format"
                    )

        # Initialize analysis repository
        repo = AnalysisRepository(db)
        
        # Retrieve performance data
        performance_data = await repo.get_player_performance_timeline(
            player_id=player_id,
            time_range=time_range,
            start_date=start_date,
            end_date=end_date
        )
        
        # Set cache control headers
        if response:
            response.headers["Cache-Control"] = "public, max-age=300"
        
        if not performance_data:
            raise HTTPException(
                status_code=404,
                detail="No performance data found for player"
            )
            
        return performance_data
        
    except ValueError as e:
        error_id = datetime.utcnow().isoformat()
        logger.error(f"Error ID {error_id}: {str(e)}", exc_info=e)
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        error_id = datetime.utcnow().isoformat()
        logger.error(f"Error ID {error_id}: Failed to analyze player performance", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to analyze player performance",
                "error_id": error_id,
                "message": str(e)
            }
        )

@app.get(
    "/players/{player_id}/openings",
    response_model=List[OpeningStatsResponse],
    responses={
        200: {"description": "Successfully retrieved opening statistics"},
        404: {"description": "Player not found or no opening data available"},
        500: {"description": "Internal server error during analysis"}
    }
)
async def get_player_openings(
    player_id: int,
    min_games: int = Field(5, ge=1, description="Minimum games threshold"),
    response: Response = None,
    db: AsyncSession = Depends(get_db)
) -> List[OpeningStatsResponse]:
    """
    Get statistics about a player's performance with different openings.
    
    Args:
        player_id: Database ID of the player
        min_games: Minimum number of games required for opening analysis
        response: FastAPI Response object for header manipulation
        db: Database session
        
    Returns:
        List[OpeningStatsResponse]: Opening statistics for the player
        
    Raises:
        HTTPException: If player is not found or analysis fails
    """
    try:
        # Initialize analysis repository
        repo = AnalysisRepository(db)
        
        # Retrieve opening statistics
        opening_stats = await repo.get_player_opening_stats(
            player_id=player_id,
            min_games=min_games
        )
        
        # Set cache control headers
        if response:
            response.headers["Cache-Control"] = "public, max-age=300"
        
        if not opening_stats:
            raise HTTPException(
                status_code=404,
                detail="No opening statistics found for player"
            )
            
        return opening_stats
        
    except ValueError as e:
        error_id = datetime.utcnow().isoformat()
        logger.error(f"Error ID {error_id}: {str(e)}", exc_info=e)
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        error_id = datetime.utcnow().isoformat()
        logger.error(f"Error ID {error_id}: Failed to analyze opening statistics", exc_info=e)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to analyze opening statistics",
                "error_id": error_id,
                "message": str(e)
            }
        )
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)