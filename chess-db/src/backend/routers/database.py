"""Database metrics and monitoring endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import logging

from database import get_session
from repository.analysis.repository import AnalysisRepository
from repository.models import DatabaseMetricsResponse
from config import DB_HOST, DB_PORT, DB_NAME

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/metrics", response_model=DatabaseMetricsResponse)
async def get_database_metrics(db: AsyncSession = Depends(get_session)):
    """Get comprehensive database metrics including performance, health, and storage metrics."""
    repository = AnalysisRepository(db)
    return await repository.get_database_metrics()
