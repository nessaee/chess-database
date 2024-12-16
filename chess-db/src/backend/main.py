from fastapi import FastAPI, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
import uvicorn
from contextlib import asynccontextmanager
import logging
from sqlalchemy import text

from database import (
    create_tables,
    dispose_tables,
    get_session,
    init_models
)

from repository import (
    GameRepository,
    PlayerRepository,
    AnalysisRepository
)

from routers.games import router as game_router
from routers.players import router as player_router
from routers.analysis import router as analysis_router
from config import CORS_ORIGINS, API_VERSION

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    Handles database initialization and cleanup.
    """
    # Startup
    logger.info("Starting API server...")
    await create_tables()
    await init_models()
    yield
    # Shutdown
    logger.info("Shutting down API server...")
    await dispose_tables()

app = FastAPI(
    title="Chess Database API",
    description="API for managing and analyzing chess games",
    version=API_VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check API and database health."""
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": str(e)}
        )

# Register routers
app.include_router(game_router)
app.include_router(player_router)
app.include_router(analysis_router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=4
    )