from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import datetime

from app.core.database import Base


# SQLAlchemy ORM models
class ModelTraining(Base):
    __tablename__ = "model_training"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    model_type = Column(String(50), nullable=False)
    parameters = Column(JSON)
    status = Column(String(20), default="pending")
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    accuracy = Column(Float)
    error_rate = Column(Float)
    user_id = Column(Integer, ForeignKey("user.id"))
    
    # Relationships
    user = relationship("User")


class TrainingData(Base):
    __tablename__ = "training_data"

    id = Column(Integer, primary_key=True, index=True)
    model_training_id = Column(Integer, ForeignKey("model_training.id"))
    data_path = Column(String(255))
    data_type = Column(String(50))
    validation_split = Column(Float, default=0.2)
    
    # Relationships
    model_training = relationship("ModelTraining")


# Pydantic models for API
class ModelTrainingBase(BaseModel):
    name: str
    description: Optional[str] = None
    model_type: str
    parameters: Optional[Dict[str, Any]] = {}


class ModelTrainingCreate(ModelTrainingBase):
    pass


class ModelTrainingUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    accuracy: Optional[float] = None
    error_rate: Optional[float] = None


class ModelTrainingResponse(ModelTrainingBase):
    id: int
    status: str
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    accuracy: Optional[float] = None
    error_rate: Optional[float] = None
    user_id: int
    
    class Config:
        from_attributes = True


class TrainingDataBase(BaseModel):
    data_type: str
    validation_split: Optional[float] = 0.2


class TrainingDataCreate(TrainingDataBase):
    model_training_id: int


class TrainingDataResponse(TrainingDataBase):
    id: int
    model_training_id: int
    data_path: Optional[str] = None
    
    class Config:
        from_attributes = True


class MTRequestDTO(BaseModel):
    model_type: str
    parameters: Dict[str, Any]
    training_data_id: int


class MTResponseDTO(BaseModel):
    success: bool
    message: str
    model_id: Optional[int] = None
    accuracy: Optional[float] = None
    error_rate: Optional[float] = None