from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# SQLAlchemy Model
class ItemDB(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models for API
class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(ItemBase):
    name: Optional[str] = None

class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PlayerResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class PlayerDB(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

class GameDB(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    white_player_id = Column(Integer, ForeignKey("players.id"))
    black_player_id = Column(Integer, ForeignKey("players.id"))
    date = Column(Date)
    result = Column(String(10))
    eco = Column(String(10))
    moves = Column(Text)
    
    white_player = relationship("PlayerDB", foreign_keys=[white_player_id])
    black_player = relationship("PlayerDB", foreign_keys=[black_player_id])

# Pydantic Models for API
class GameResponse(BaseModel):
    id: int
    white_player_id: int
    black_player_id: int
    white_player: Optional[PlayerResponse] = None
    black_player: Optional[PlayerResponse] = None
    date: Optional[datetime] = None
    result: str
    eco: Optional[str] = None
    moves: str
    model_config = ConfigDict(from_attributes=True)