"""
Database configuration and session management for the chess database.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import NullPool
from config import DATABASE_URL
import os
import logging
from repository.models.base import Base
from repository.models.player import PlayerDB
from repository.models.game import GameDB
from datetime import datetime

logger = logging.getLogger(__name__)

logger.info(f"Creating database engine with URL: {DATABASE_URL}")
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Enable SQL logging
    poolclass=NullPool,  # Disable connection pooling in development
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,  # Recycle connections after 1 hour
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def create_tables():
    """Create database tables if they don't exist"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
        
async def dispose_tables():
    """Clean up database connections"""
    await engine.dispose()
    logger.info("Database connections disposed")

async def init_models():
    """Initialize any required model data"""
    async with async_session() as session:
        try:
            # Check if we need to initialize data
            query = select(func.count()).select_from(PlayerDB)
            result = await session.execute(query)
            count = result.scalar()
            
            if count == 0:
                logger.info("Database is empty")
                pass
            else:
                logger.info("Database already contains data, skipping initialization")
                
        except Exception as e:
            logger.error(f"Error initializing models: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    logger.info("Models initialized")

async def get_session() -> AsyncSession:
    """Get a database session."""
    try:
        async with async_session() as session:
            # Enable relationship loading
            session.expire_on_commit = False
            yield session
    except Exception as e:
        logger.error(f"Error in database session: {e}")
        raise

async def check_connection() -> bool:
    """Check if database connection is working"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False