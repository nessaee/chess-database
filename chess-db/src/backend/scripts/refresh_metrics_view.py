#!/usr/bin/env python3
"""Script to refresh the endpoint metrics materialized view."""

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from config import DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def refresh_metrics_view():
    """Refresh the endpoint_performance_stats materialized view."""
    try:
        engine = create_async_engine(DATABASE_URL)
        async with engine.begin() as conn:
            await conn.execute(text("SELECT refresh_endpoint_performance_stats()"))
            logger.info("Successfully refreshed endpoint_performance_stats view")
    except Exception as e:
        logger.error(f"Error refreshing endpoint_performance_stats view: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(refresh_metrics_view())
