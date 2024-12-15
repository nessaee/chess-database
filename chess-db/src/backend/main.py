# main.py
from fastapi import FastAPI, Request, Response,Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from fastapi.exceptions import HTTPException
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import sys

from sqlalchemy.ext.asyncio import AsyncSession
from database import init_db, get_db

from repository import AnalysisRepository
from routers import analysis_router, game_router, item_router
from config import CORS_ORIGINS, API_VERSION

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

# Security schemes
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

def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="Chess Analysis API",
        description="API for chess game analysis and statistics",
        version=API_VERSION,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=3600
    )

    # Register routers
    app.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
    app.include_router(game_router, prefix="/games", tags=["Games"])
    app.include_router(item_router, prefix="/items", tags=["Items"])

    # Register global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
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

    # Health check endpoint
    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "chess-backend",
            "version": API_VERSION
        }

    @app.get("/players/search")
    async def search_players(
        q: str,
        db: AsyncSession = Depends(get_db)
    ):
        """Search players by name"""
        try:
            repository = AnalysisRepository(db)
            results = await repository.search_players(q)
            return JSONResponse(
                content=results,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Cache-Control": "public, max-age=30"
                }
            )
        except Exception as e:
            logger.error(f"Player search error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to search players"
            )
    return app

    
app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=4
    )