import time
import csv
import os
from datetime import datetime
from fastapi import Request, Response
from typing import Callable
import asyncio
import logging

logger = logging.getLogger(__name__)

class LatencyMonitor:
    HEADERS = ['timestamp', 'method', 'endpoint', 'latency_ms', 'status_code', 'response_size_bytes']

    def __init__(self, log_file: str = "logs/query_latency.csv"):
        self.log_file = log_file
        self._ensure_log_file_exists()
        self._ensure_headers_first()

    def _ensure_log_file_exists(self):
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.HEADERS)

    def _ensure_headers_first(self):
        if not os.path.exists(self.log_file) or os.path.getsize(self.log_file) == 0:
            return

        # Read the current content
        with open(self.log_file, 'r', newline='') as f:
            reader = csv.reader(f)
            first_row = next(reader, None)
            if first_row != self.HEADERS:
                # Store all rows
                rows = [first_row] + list(reader) if first_row else list(reader)
                
                # Rewrite file with headers first
                with open(self.log_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(self.HEADERS)
                    writer.writerows(rows)

    async def log_request_latency(self, request: Request, call_next: Callable):
        start_time = time.time()
        response = await call_next(request)
        end_time = time.time()
        
        latency_ms = round((end_time - start_time) * 1000, 2)
        timestamp = datetime.now().isoformat()
        
        # Get response content and size
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        response_size = len(response_body)
        
        # Log to CSV file
        try:
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    request.method,
                    request.url.path,
                    latency_ms,
                    response.status_code,
                    response_size
                ])
        except Exception as e:
            logger.error(f"Failed to log request latency: {str(e)}")
        
        # Add latency header to response
        response.headers["X-Response-Time"] = f"{latency_ms}ms"
        response.headers["X-Response-Size"] = f"{response_size} bytes"
        
        # Create new response with the captured body
        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
