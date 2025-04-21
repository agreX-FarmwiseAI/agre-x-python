from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import time
import json
import random

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.model_training import (
    ModelTraining, ModelTrainingCreate, ModelTrainingUpdate, ModelTrainingResponse,
    TrainingData, TrainingDataCreate, TrainingDataResponse,
    MTRequestDTO, MTResponseDTO
)
from app.models.user import User
from app.core.exceptions import ResourceNotFoundException
from app.services.model_training import run_model_training

router = APIRouter()


@router.post("/", response_model=ModelTrainingResponse, status_code=status.HTTP_201_CREATED)
async def create_model_training(
    model_training: ModelTrainingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new model training job
    """
    db_model_training = ModelTraining(
        name=model_training.name,
        description=model_training.description,
        model_type=model_training.model_type,
        parameters=model_training.parameters,
        user_id=current_user.id,
        status="pending"
    )
    db.add(db_model_training)
    db.commit()
    db.refresh(db_model_training)
    return db_model_training


@router.get("/", response_model=List[ModelTrainingResponse])
async def get_model_trainings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all model training jobs for the current user
    """
    model_trainings = db.query(ModelTraining).filter(
        ModelTraining.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return model_trainings


@router.get("/{model_training_id}", response_model=ModelTrainingResponse)
async def get_model_training(
    model_training_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a model training job by ID
    """
    model_training = db.query(ModelTraining).filter(ModelTraining.id == model_training_id).first()
    if not model_training:
        raise ResourceNotFoundException("ModelTraining", model_training_id)
    
    # Check if user is authorized
    if model_training.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this model training job"
        )
    
    return model_training


@router.put("/{model_training_id}", response_model=ModelTrainingResponse)
async def update_model_training(
    model_training_id: int,
    model_training_update: ModelTrainingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a model training job
    """
    model_training = db.query(ModelTraining).filter(ModelTraining.id == model_training_id).first()
    if not model_training:
        raise ResourceNotFoundException("ModelTraining", model_training_id)
    
    # Check if user is authorized
    if model_training.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this model training job"
        )
    
    # Update fields if provided
    if model_training_update.name is not None:
        model_training.name = model_training_update.name
    if model_training_update.description is not None:
        model_training.description = model_training_update.description
    if model_training_update.status is not None:
        model_training.status = model_training_update.status
    if model_training_update.accuracy is not None:
        model_training.accuracy = model_training_update.accuracy
    if model_training_update.error_rate is not None:
        model_training.error_rate = model_training_update.error_rate
    
    db.commit()
    db.refresh(model_training)
    return model_training


@router.delete("/{model_training_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_training(
    model_training_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a model training job
    """
    model_training = db.query(ModelTraining).filter(ModelTraining.id == model_training_id).first()
    if not model_training:
        raise ResourceNotFoundException("ModelTraining", model_training_id)
    
    # Check if user is authorized
    if model_training.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this model training job"
        )
    
    # Delete model training and related data
    db.delete(model_training)
    db.commit()
    return None


@router.post("/training-data", response_model=TrainingDataResponse, status_code=status.HTTP_201_CREATED)
async def create_training_data(
    training_data: TrainingDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create training data for a model
    """
    # Check if model training exists
    model_training = db.query(ModelTraining).filter(ModelTraining.id == training_data.model_training_id).first()
    if not model_training:
        raise ResourceNotFoundException("ModelTraining", training_data.model_training_id)
    
    # Check if user is authorized
    if model_training.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this model training job"
        )
    
    db_training_data = TrainingData(
        model_training_id=training_data.model_training_id,
        data_type=training_data.data_type,
        validation_split=training_data.validation_split
    )
    db.add(db_training_data)
    db.commit()
    db.refresh(db_training_data)
    return db_training_data


@router.post("/train", response_model=MTResponseDTO)
async def train_model(
    request: MTRequestDTO,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Start a model training job
    """
    # Check if training data exists
    training_data = db.query(TrainingData).filter(TrainingData.id == request.training_data_id).first()
    if not training_data:
        raise ResourceNotFoundException("TrainingData", request.training_data_id)
    
    # Check if model training exists
    model_training = db.query(ModelTraining).filter(ModelTraining.id == training_data.model_training_id).first()
    if not model_training:
        raise ResourceNotFoundException("ModelTraining", training_data.model_training_id)
    
    # Check if user is authorized
    if model_training.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to train this model"
        )
    
    # Update model training job
    model_training.status = "running"
    model_training.model_type = request.model_type
    model_training.parameters = request.parameters
    db.commit()
    
    # Run model training in background
    background_tasks.add_task(
        run_model_training,
        model_training_id=model_training.id,
        training_data_id=training_data.id,
        db=db
    )
    
    return MTResponseDTO(
        success=True,
        message=f"Model training job started with ID {model_training.id}",
        model_id=model_training.id
    )