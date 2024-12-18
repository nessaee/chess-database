"""Main FastAPI application module."""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from database import get_session
from middleware.performance import PerformanceMiddleware
from middleware.metrics import MetricsMiddleware
from routers import game_router, player_router, analysis_router, database_router
from config import CORS_ORIGINS, API_VERSION, DB_HOST, DB_PORT, DB_NAME
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("main")

# Create FastAPI app
app = FastAPI(
    title="Chess Analytics API",
    description="API for analyzing chess games and player statistics",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics monitoring middleware
app.add_middleware(MetricsMiddleware)

# Add performance monitoring middleware
app.add_middleware(PerformanceMiddleware, db_func=get_session)

# Mount routers
app.include_router(game_router, prefix="/api/games", tags=["games"])
app.include_router(player_router, prefix="/api/players", tags=["players"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["analysis"])
app.include_router(database_router, prefix="/api/database", tags=["database"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        async for db in get_session():
            await db.execute(text("SELECT 1"))
            return {
                "status": "healthy",
                "database": "connected",
                "version": API_VERSION
            }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "details": {
                    "host": DB_HOST,
                    "port": DB_PORT,
                    "database": DB_NAME
                }
            }
        )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
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