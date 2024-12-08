from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:chesspass@db:5432/itemsdb")

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def init_db():
    """Initialize database tables if they don't exist"""
    async with engine.begin() as conn:
        # Get list of existing tables using SQLAlchemy's text construct
        result = await conn.execute(
            text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """)
        )
        existing_tables = {row[0] for row in result}
        
        # Only create tables that don't exist
        if not existing_tables:
            await conn.run_sync(Base.metadata.create_all)
            print("Created database tables.")
        else:
            print("Database tables already exist, skipping creation.")