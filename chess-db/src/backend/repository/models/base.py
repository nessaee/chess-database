"""
Base models and common utilities for the chess database.

This module provides:
1. SQLAlchemy base class and common column types
2. Pydantic base models for API responses
3. Common type definitions and utilities
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date,
    ForeignKey, Boolean, Float, Enum, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any, TypeVar, Generic

# Create base class for SQLAlchemy models
Base = declarative_base()

# Re-export commonly used types
__all__ = [
    # SQLAlchemy components
    'Base', 'Column', 'Integer', 'String', 'Text',
    'DateTime', 'Date', 'ForeignKey', 'relationship',
    'Boolean', 'Float', 'Enum', 'JSON',
    
    # Pydantic components
    'BaseModel', 'ConfigDict', 'Field',
    
    # Type hints
    'Optional', 'List', 'Dict', 'Any', 'TypeVar', 'Generic'
]
