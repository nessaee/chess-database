from fastapi import FastAPI, Depends, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from typing import List, Dict, Union, Optional
import logging
import sys
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import status
from fastapi.security import APIKeyHeader
from database import SessionLocal, init_db
from repository import ItemRepository, GameRepository, AnalysisRepository
from models import (
    ItemCreate, ItemUpdate, ItemResponse, GameResponse,
    PlayerPerformanceResponse, OpeningStatsResponse, MoveCountAnalysis
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('api.log')
    ]
)

logger = logging.getLogger(__name__)

# API Key security scheme
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    try:
        await init_db()
        logger.info("Application startup completed")
        yield
    finally:
        logger.info("Application shutdown completed")

# Initialize FastAPI application
app = FastAPI(
    title="Chess Analysis API",
    description="API for chess game analysis and statistics",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://frontend:5173",
        "http://192.168.1.30:5173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# Database session dependency
async def get_db() -> AsyncSession:
    """Database session manager"""
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    error_id = datetime.utcnow().isoformat()
    logger.error(f"Error ID: {error_id}", exc_info=exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "error_id": error_id,
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "chess-backend",
        "version": "1.0.0"
    }

# Item endpoints
@app.post("/items", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new item"""
    repo = ItemRepository(db)
    return await repo.create_item(item)

@app.get("/items", response_model=List[ItemResponse])
async def read_items(db: AsyncSession = Depends(get_db)):
    """Get all items"""
    repo = ItemRepository(db)
    return await repo.get_items()

@app.get("/items/{item_id}", response_model=ItemResponse)
async def read_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """Get specific item"""
    repo = ItemRepository(db)
    item = await repo.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item: ItemUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update item"""
    repo = ItemRepository(db)
    updated_item = await repo.update_item(item_id, item)
    if updated_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item

@app.delete("/items/{item_id}")
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    """Delete item"""
    repo = ItemRepository(db)
    success = await repo.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ok": True}

# Game endpoints
@app.get("/games", response_model=List[GameResponse])
async def read_games(
    response: Response,
    player_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get games with filtering"""
    repo = GameRepository(db)
    games = await repo.get_games(
        player_name=player_name,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    response.headers["Cache-Control"] = "public, max-age=300"
    return games

@app.get("/games/{game_id}", response_model=GameResponse)
async def read_game(game_id: int, db: AsyncSession = Depends(get_db)):
    """Get specific game"""
    repo = GameRepository(db)
    game = await repo.get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

@app.get("/players/{player_id}/games", response_model=List[GameResponse])
async def read_player_games(player_id: int, db: AsyncSession = Depends(get_db)):
    """Get games for specific player"""
    repo = GameRepository(db)
    games = await repo.get_player_games(player_id)
    if not games:
        raise HTTPException(status_code=404, detail="No games found for this player")
    return games

@app.get("/stats/games")
async def get_game_stats(db: AsyncSession = Depends(get_db)):
    """Get game statistics"""
    repo = GameRepository(db)
    return await repo.get_game_stats()

# Analysis endpoints
@app.get("/analysis/move-counts", response_model=List[MoveCountAnalysis])
async def get_move_count_distribution(
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Get move count distribution"""
    try:
        repo = AnalysisRepository(db)
        results = await repo.get_move_count_distribution()
        response.headers["Cache-Control"] = "public, max-age=300"
        return results
    except Exception as e:
        logger.error(f"Error analyzing move counts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze move counts"
        )

@app.get("/players/{player_id}/performance", response_model=List[PlayerPerformanceResponse])
async def get_player_performance(
    player_id: int,
    time_range: str = 'monthly',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    response: Response = None,
    db: AsyncSession = Depends(get_db)
):
    """Get player performance statistics"""
    try:
        repo = AnalysisRepository(db)
        performance_data = await repo.get_player_performance_timeline(
            player_id=player_id,
            time_range=time_range,
            start_date=start_date,
            end_date=end_date
        )
        
        if response:
            response.headers["Cache-Control"] = "public, max-age=300"
        
        if not performance_data:
            raise HTTPException(
                status_code=404,
                detail="No performance data found for player"
            )
        
        return performance_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/players/{player_id}/openings", response_model=List[OpeningStatsResponse])
async def get_player_openings(
    player_id: int,
    min_games: int = 5,
    response: Response = None,
    db: AsyncSession = Depends(get_db)
):
    """Get player opening statistics"""
    try:
        repo = AnalysisRepository(db)
        opening_stats = await repo.get_player_opening_stats(
            player_id=player_id,
            min_games=min_games
        )
        
        if response:
            response.headers["Cache-Control"] = "public, max-age=300"
        
        if not opening_stats:
            raise HTTPException(
                status_code=404,
                detail="No opening statistics found for player"
            )
        
        return opening_stats
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=4
    )