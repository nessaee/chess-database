import time
from typing import Callable, Dict, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
from database import async_session
import json
from sqlalchemy.dialects.postgresql import JSONB

logger = logging.getLogger(__name__)

class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Start timing the request
        start_time = time.time()
        response = None
        error_message = None

        try:
            # Process the request
            response = await call_next(request)
            return response
        except Exception as e:
            # Capture error details
            error_message = str(e)
            raise
        finally:
            if not request.url.path.startswith(("/docs", "/openapi.json", "/metrics")):
                # Calculate metrics
                end_time = time.time()
                response_time_ms = round((end_time - start_time) * 1000, 2)
                
                # Get response details
                status_code = response.status_code if response else 500
                success = status_code < 400 if response else False
                
                try:
                    await self._store_metrics(
                        request=request,
                        path=request.url.path,
                        response_time_ms=response_time_ms,
                        status_code=status_code,
                        success=success,
                        error_message=error_message,
                        response=response
                    )
                except Exception as e:
                    logger.error(f"Failed to store metrics: {e}")

    async def _store_metrics(
        self,
        request: Request,
        path: str,
        response_time_ms: float,
        status_code: int,
        success: bool,
        error_message: Optional[str],
        response: Optional[Response]
    ) -> None:
        async with async_session() as db:
            try:
                # Get response size if available
                response_size = len(response.body) if response and hasattr(response, 'body') else None
                
                # Get request parameters
                request_params = {}
                if request.query_params:
                    request_params["query"] = dict(request.query_params)
                if request.path_params:
                    request_params["path"] = dict(request.path_params)
                
                # Store metrics in database
                stmt = text(f"""
                    INSERT INTO endpoint_metrics (
                        endpoint,
                        method,
                        response_time_ms,
                        response_size_bytes,
                        status_code,
                        success,
                        error_message,
                        request_params
                    ) VALUES (
                        :endpoint,
                        :method,
                        :response_time_ms,
                        :response_size_bytes,
                        :status_code,
                        :success,
                        :error_message,
                        cast(:request_params AS jsonb)
                    )
                """).bindparams(
                    endpoint=path,
                    method=request.method,
                    response_time_ms=response_time_ms,
                    response_size_bytes=response_size,
                    status_code=status_code,
                    success=success,
                    error_message=error_message,
                    request_params=json.dumps(request_params) if request_params else None
                )
                
                await db.execute(stmt)
                await db.commit()
                
            except Exception as e:
                logger.error(f"Error storing metrics: {e}")
                try:
                    await db.rollback()
                except Exception as rollback_error:
                    logger.error(f"Error during rollback: {rollback_error}")
