from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.analysis import (
    Crop, CropCreate, CropResponse,
    Satellite, SatelliteCreate, SatelliteResponse, SatelliteDetail,
    Polarization, PolarizationCreate, PolarizationResponse,
    Calibration, CalibrationCreate, CalibrationResponse,
    MaskNoise, MaskNoiseCreate, MaskNoiseResponse
)
from app.models.user import User
from app.core.exceptions import ResourceNotFoundException

router = APIRouter()


@router.post("/crops", response_model=CropResponse, status_code=status.HTTP_201_CREATED)
async def create_crop(
    crop: CropCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new crop
    """
    db_crop = Crop(
        name=crop.name,
        description=crop.description,
        growth_period=crop.growth_period,
        water_requirements=crop.water_requirements
    )
    db.add(db_crop)
    db.commit()
    db.refresh(db_crop)
    return db_crop


@router.get("/crops", response_model=List[CropResponse])
async def get_crops(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all crops
    """
    crops = db.query(Crop).offset(skip).limit(limit).all()
    return crops


@router.get("/crops/{crop_id}", response_model=CropResponse)
async def get_crop(
    crop_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a crop by ID
    """
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise ResourceNotFoundException("Crop", crop_id)
    return crop


@router.post("/satellites", response_model=SatelliteResponse, status_code=status.HTTP_201_CREATED)
async def create_satellite(
    satellite: SatelliteCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new satellite
    """
    db_satellite = Satellite(
        name=satellite.name,
        description=satellite.description,
        resolution=satellite.resolution
    )
    db.add(db_satellite)
    db.commit()
    db.refresh(db_satellite)
    return db_satellite


@router.get("/satellites", response_model=List[SatelliteResponse])
async def get_satellites(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all satellites
    """
    satellites = db.query(Satellite).offset(skip).limit(limit).all()
    return satellites


@router.get("/satellites/{satellite_id}", response_model=SatelliteDetail)
async def get_satellite(
    satellite_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a satellite by ID with its polarizations
    """
    satellite = db.query(Satellite).filter(Satellite.id == satellite_id).first()
    if not satellite:
        raise ResourceNotFoundException("Satellite", satellite_id)
    return satellite


@router.post("/polarizations", response_model=PolarizationResponse, status_code=status.HTTP_201_CREATED)
async def create_polarization(
    polarization: PolarizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new polarization
    """
    # Check if satellite exists
    satellite = db.query(Satellite).filter(Satellite.id == polarization.satellite_id).first()
    if not satellite:
        raise ResourceNotFoundException("Satellite", polarization.satellite_id)
    
    db_polarization = Polarization(
        name=polarization.name,
        description=polarization.description,
        satellite_id=polarization.satellite_id
    )
    db.add(db_polarization)
    db.commit()
    db.refresh(db_polarization)
    return db_polarization


@router.get("/polarizations", response_model=List[PolarizationResponse])
async def get_polarizations(
    db: Session = Depends(get_db),
    satellite_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get all polarizations, optionally filtered by satellite
    """
    query = db.query(Polarization)
    if satellite_id:
        query = query.filter(Polarization.satellite_id == satellite_id)
    
    polarizations = query.offset(skip).limit(limit).all()
    return polarizations


@router.post("/calibrations", response_model=CalibrationResponse, status_code=status.HTTP_201_CREATED)
async def create_calibration(
    calibration: CalibrationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new calibration
    """
    # Check if crop exists
    crop = db.query(Crop).filter(Crop.id == calibration.crop_id).first()
    if not crop:
        raise ResourceNotFoundException("Crop", calibration.crop_id)
    
    # Check if satellite exists
    satellite = db.query(Satellite).filter(Satellite.id == calibration.satellite_id).first()
    if not satellite:
        raise ResourceNotFoundException("Satellite", calibration.satellite_id)
    
    db_calibration = Calibration(
        crop_id=calibration.crop_id,
        satellite_id=calibration.satellite_id,
        coefficient=calibration.coefficient,
        confidence=calibration.confidence
    )
    db.add(db_calibration)
    db.commit()
    db.refresh(db_calibration)
    return db_calibration


@router.get("/calibrations", response_model=List[CalibrationResponse])
async def get_calibrations(
    db: Session = Depends(get_db),
    crop_id: Optional[int] = None,
    satellite_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get all calibrations, optionally filtered by crop or satellite
    """
    query = db.query(Calibration)
    if crop_id:
        query = query.filter(Calibration.crop_id == crop_id)
    if satellite_id:
        query = query.filter(Calibration.satellite_id == satellite_id)
    
    calibrations = query.offset(skip).limit(limit).all()
    return calibrations


@router.post("/mask-noise", response_model=MaskNoiseResponse, status_code=status.HTTP_201_CREATED)
async def create_mask_noise(
    mask_noise: MaskNoiseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new mask noise
    """
    db_mask_noise = MaskNoise(
        name=mask_noise.name,
        description=mask_noise.description,
        mask_type=mask_noise.mask_type,
        noise_level=mask_noise.noise_level
    )
    db.add(db_mask_noise)
    db.commit()
    db.refresh(db_mask_noise)
    return db_mask_noise


@router.get("/mask-noise", response_model=List[MaskNoiseResponse])
async def get_mask_noise(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all mask noise entries
    """
    mask_noise_entries = db.query(MaskNoise).offset(skip).limit(limit).all()
    return mask_noise_entries