"""Models for request logging and monitoring."""

from datetime import datetime
from .base import Base, Column, Integer, String, DateTime, Float

class RequestLog(Base):
    """Model for logging API request metrics."""
    __tablename__ = 'request_logs'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time = Column(Float, nullable=False)  # in milliseconds
    response_size = Column(Integer, nullable=False)  # in bytes
    client_ip = Column(String)
    user_agent = Column(String)
