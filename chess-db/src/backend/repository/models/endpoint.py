"""Models for endpoint metrics and performance tracking."""

from datetime import datetime
from .base import Base, Column, Integer, String, DateTime, Float

class EndpointMetrics(Base):
    """Model for tracking API endpoint performance metrics."""
    __tablename__ = 'endpoint_metrics'

    id = Column(Integer, primary_key=True)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time = Column(Float, nullable=False)  # in milliseconds
    response_size = Column(Integer, nullable=False)  # in bytes
