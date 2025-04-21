from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List
import datetime

from app.core.database import Base


# SQLAlchemy ORM models
class Crop(Base):
    __tablename__ = "crop"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    growth_period = Column(Integer)  # in days
    water_requirements = Column(Float)
    
    # Relationships
    calibration = relationship("Calibration", back_populates="crop")


# class Satellite(Base):
#     __tablename__ = "satellite"

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(100), nullable=False)
#     description = Column(Text)
#     resolution = Column(Float)  # in meters
    
#     # Relationships
#     calibration = relationship("Calibration", back_populates="satellite")
#     polarization = relationship("Polarization", back_populates="satellite")


class Polarization(Base):
    __tablename__ = "polarization"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    satellite_id = Column(Integer, ForeignKey("satellite.id"))
    
    # Relationships
    satellite = relationship("Satellite", back_populates="polarization")


class Calibration(Base):
    __tablename__ = "calibration"

    id = Column(Integer, primary_key=True, index=True)
    crop_id = Column(Integer, ForeignKey("crop.id"))
    satellite_id = Column(Integer, ForeignKey("satellite.id"))
    coefficient = Column(Float, nullable=False)
    confidence = Column(Float)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    crop = relationship("Crop", back_populates="calibration")
    satellite = relationship("Satellite", back_populates="calibration")


class MaskNoise(Base):
    __tablename__ = "mask_noise"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    mask_type = Column(String(50))
    noise_level = Column(Float)


# Pydantic models for API
class CropBase(BaseModel):
    name: str
    description: Optional[str] = None
    growth_period: Optional[int] = None
    water_requirements: Optional[float] = None


class CropCreate(CropBase):
    pass


class CropResponse(CropBase):
    id: int
    
    class Config:
        from_attributes = True


class SatelliteBase(BaseModel):
    name: str
    description: Optional[str] = None
    resolution: Optional[float] = None


class SatelliteCreate(SatelliteBase):
    pass


class SatelliteResponse(SatelliteBase):
    id: int
    
    class Config:
        from_attributes = True


class PolarizationBase(BaseModel):
    name: str
    description: Optional[str] = None
    satellite_id: int


class PolarizationCreate(PolarizationBase):
    pass


class PolarizationResponse(PolarizationBase):
    id: int
    
    class Config:
        from_attributes = True


class CalibrationBase(BaseModel):
    crop_id: int
    satellite_id: int
    coefficient: float
    confidence: Optional[float] = None


class CalibrationCreate(CalibrationBase):
    pass


class CalibrationResponse(CalibrationBase):
    id: int
    created_at: datetime.datetime
    
    class Config:
        from_attributes = True


class MaskNoiseBase(BaseModel):
    name: str
    description: Optional[str] = None
    mask_type: str
    noise_level: float


class MaskNoiseCreate(MaskNoiseBase):
    pass


class MaskNoiseResponse(MaskNoiseBase):
    id: int
    
    class Config:
        from_attributes = True


class SatelliteDetail(SatelliteResponse):
    polarizations: List[PolarizationResponse] = []
    
    class Config:
        from_attributes = True