"""Middleware for tracking API endpoint performance."""

import time
import json
from typing import Callable, Union
from fastapi import Request, Response
from fastapi.responses import JSONResponse as FastAPIJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, JSONResponse, StreamingResponse
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking API endpoint performance."""
    
    def __init__(self, app: ASGIApp, db_func: Callable[[], AsyncSession]):
        super().__init__(app)
        self.get_db = db_func
    
    def calculate_response_size(self, response: Response) -> int:
        """Calculate the size of the response in bytes.
        
        Args:
            response: The response object to calculate size for
            
        Returns:
            int: Size of the response in bytes
        """
        try:
            # Handle streaming responses
            if isinstance(response, StreamingResponse):
                # Try to get the response content if it's already generated
                if hasattr(response, '_content'):
                    content = response._content
                    if isinstance(content, bytes):
                        return len(content)
                    elif isinstance(content, str):
                        return len(content.encode('utf-8'))
                # If content is not available, estimate from headers
                elif 'content-length' in response.headers:
                    try:
                        return int(response.headers['content-length'])
                    except (ValueError, TypeError):
                        pass
                logger.debug("StreamingResponse size cannot be calculated accurately")
                return 0
            
            # Handle JSON responses from FastAPI and Starlette
            if isinstance(response, (JSONResponse, FastAPIJSONResponse)):
                # Access the raw response content
                content = response.body
                if isinstance(content, bytes):
                    return len(content)
                # If somehow not bytes, encode it
                return len(json.dumps(response.body).encode('utf-8'))
            
            # Handle raw response body
            if hasattr(response, 'body'):
                content = response.body
                if content is None:
                    return 0
                if isinstance(content, bytes):
                    return len(content)
                if isinstance(content, str):
                    return len(content.encode('utf-8'))
                if isinstance(content, (dict, list)):
                    return len(json.dumps(content).encode('utf-8'))
                # For other types, try string conversion
                return len(str(content).encode('utf-8'))
            
            # If response has no body attribute but has raw_body
            if hasattr(response, 'raw_body'):
                content = response.raw_body
                if isinstance(content, bytes):
                    return len(content)
                return len(str(content).encode('utf-8'))
            
            # Try to get size from content-length header
            if 'content-length' in response.headers:
                try:
                    return int(response.headers['content-length'])
                except (ValueError, TypeError):
                    pass
            
            logger.debug(f"Unable to determine size for response type: {type(response)}")
            return 0
            
        except Exception as e:
            logger.error(f"Error calculating response size: {str(e)}")
            return 0
    
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()
        response = None
        
        try:
            # Get response first
            response = await call_next(request)
            
            # Calculate metrics
            response_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
            response_size = self.calculate_response_size(response)
            
            # Log response details for debugging
            logger.debug(
                f"Response type: {type(response)}, "
                f"Has body: {hasattr(response, 'body')}, "
                f"Has raw_body: {hasattr(response, 'raw_body')}, "
                f"Size: {response_size}"
            )
            
            success = 200 <= response.status_code < 300
            
            # Extract request parameters, excluding sensitive data
            request_params = {
                k: str(v) for k, v in request.query_params.items()
                if k.lower() not in {'password', 'token', 'key', 'secret', 'auth'}
            }
            
            # Get error message if any
            error_message = None
            if not success:
                try:
                    if hasattr(response, 'body'):
                        if isinstance(response.body, bytes):
                            error_message = response.body.decode('utf-8')
                        else:
                            error_message = str(response.body)
                except Exception as e:
                    error_message = str(e)
            
            # Log request details
            logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Size: {response_size} bytes - "
                f"Duration: {response_time}ms"
            )
            
            # Record metrics in database
            async for db in self.get_db():
                try:
                    query = """
                        INSERT INTO endpoint_metrics (
                            endpoint,
                            method,
                            response_time_ms,
                            response_size_bytes,
                            status_code,
                            success,
                            request_params,
                            error_message
                        ) VALUES (
                            :endpoint,
                            :method,
                            :response_time,
                            :response_size,
                            :status_code,
                            :success,
                            cast(:request_params AS jsonb),
                            :error_message
                        )
                    """
                    
                    stmt = text(query).bindparams(
                        endpoint=str(request.url.path),
                        method=request.method,
                        response_time=response_time,
                        response_size=response_size,
                        status_code=response.status_code,
                        success=success,
                        request_params=json.dumps(request_params),
                        error_message=error_message
                    )
                    
                    await db.execute(stmt)
                    await db.commit()
                    break
                    
                except Exception as e:
                    logger.error(f"Error recording metrics: {str(e)}")
            
            return response
            
        except Exception as e:
            # Calculate error metrics
            response_time = int((time.time() - start_time) * 1000)
            
            # Log the error
            logger.error(
                f"{request.method} {request.url.path} - "
                f"Error: {str(e)} - "
                f"Duration: {response_time}ms"
            )
            
            # Record error in database
            try:
                async for db in self.get_db():
                    try:
                        query = """
                            INSERT INTO endpoint_metrics (
                                endpoint,
                                method,
                                response_time_ms,
                                response_size_bytes,
                                status_code,
                                success,
                                error_message
                            ) VALUES (
                                :endpoint,
                                :method,
                                :response_time,
                                :response_size,
                                :status_code,
                                :success,
                                :error
                            )
                        """
                        
                        stmt = text(query).bindparams(
                            endpoint=str(request.url.path),
                            method=request.method,
                            response_time=response_time,
                            response_size=0,
                            status_code=500,
                            success=False,
                            error=str(e)
                        )
                        
                        await db.execute(stmt)
                        await db.commit()
                        break
                    except Exception as db_error:
                        logger.error(f"Error recording error metrics: {str(db_error)}")
            except Exception as outer_error:
                logger.error(f"Error getting database session: {str(outer_error)}")
            
            # Re-raise the original exception
            raise
