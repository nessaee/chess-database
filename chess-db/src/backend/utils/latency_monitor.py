import time
import csv
import os
from datetime import datetime
from fastapi import Request
from typing import Callable
import asyncio
import logging

logger = logging.getLogger(__name__)

class LatencyMonitor:
    def __init__(self, log_file: str = "query_latency.csv"):
        self.log_file = log_file
        self._ensure_log_file_exists()

    def _ensure_log_file_exists(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'method', 'endpoint', 'latency_ms', 'status_code'])

    async def log_request_latency(self, request: Request, call_next: Callable):
        start_time = time.time()
        response = await call_next(request)
        end_time = time.time()
        
        latency_ms = round((end_time - start_time) * 1000, 2)
        timestamp = datetime.now().isoformat()
        
        # Log to CSV file
        try:
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    request.method,
                    request.url.path,
                    latency_ms,
                    response.status_code
                ])
        except Exception as e:
            logger.error(f"Failed to log request latency: {str(e)}")
        
        # Add latency header to response
        response.headers["X-Response-Time"] = f"{latency_ms}ms"
        return response
