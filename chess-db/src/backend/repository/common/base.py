# repository/common/base.py
from typing import TypeVar, Generic, Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from .errors import DatabaseOperationError, ValidationError
from .metrics import MetricsCollector

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """
    Abstract base repository implementing common database operations.
    
    Provides foundational functionality for all repository implementations
    including query execution, error handling, and metrics collection.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            db: Active SQLAlchemy async session
        """
        self.db = db
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._metrics = MetricsCollector(namespace=self.__class__.__name__)

    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        error_msg: str = "Query execution failed"
    ) -> Any:
        """
        Execute a database query with error handling and metrics.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            error_msg: Error message prefix for exceptions
            
        Returns:
            Query result
            
        Raises:
            DatabaseOperationError: On query execution failure
        """
        start_time = datetime.now()
        try:
            result = await self.db.execute(text(query), params or {})
            
            # Record metrics
            duration = (datetime.now() - start_time).total_seconds()
            self._metrics.observe("query_duration", duration)
            
            return result
            
        except Exception as e:
            self._metrics.increment("query_errors")
            self.logger.error(
                f"{error_msg}: {str(e)}",
                extra={
                    "query": query,
                    "params": params,
                    "duration": (datetime.now() - start_time).total_seconds()
                },
                exc_info=True
            )
            raise DatabaseOperationError(f"{error_msg}: {str(e)}")

    async def begin_transaction(self):
        """Start a new database transaction."""
        return await self.db.begin()

    async def commit(self):
        """Commit current transaction."""
        await self.db.commit()

    async def rollback(self):
        """Rollback current transaction."""
        await self.db.rollback()

    async def close(self):
        """Close database session."""
        await self.db.close()

