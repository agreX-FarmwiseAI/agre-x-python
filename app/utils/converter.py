from typing import Dict, Any, List, Union, Optional, TypeVar, Generic, Type
from pydantic import BaseModel
import datetime
import json
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

T = TypeVar('T')
M = TypeVar('M')


class Converter(Generic[T, M]):
    """
    Utility class for converting between different data types
    """
    @staticmethod
    def model_to_dict(model: Any) -> Dict[str, Any]:
        """
        Convert a SQLAlchemy model to a dictionary
        
        Args:
            model: SQLAlchemy model instance
        
        Returns:
            Dictionary representation of the model
        """
        if model is None:
            return {}
        
        result = {}
        for column in model.__table__.columns:
            value = getattr(model, column.name)
            if isinstance(value, datetime.datetime):
                value = value.isoformat()
            result[column.name] = value
        
        return result
    
    @staticmethod
    def model_to_json(model: Any) -> str:
        """
        Convert a SQLAlchemy model to a JSON string
        
        Args:
            model: SQLAlchemy model instance
        
        Returns:
            JSON string representation of the model
        """
        return json.dumps(Converter.model_to_dict(model))
    
    @staticmethod
    def models_to_dicts(models: List[Any]) -> List[Dict[str, Any]]:
        """
        Convert a list of SQLAlchemy models to a list of dictionaries
        
        Args:
            models: List of SQLAlchemy model instances
        
        Returns:
            List of dictionary representations
        """
        return [Converter.model_to_dict(model) for model in models]
    
    @staticmethod
    def dict_to_model(data: Dict[str, Any], model_class: Type[T]) -> T:
        """
        Convert a dictionary to a SQLAlchemy model instance
        
        Args:
            data: Dictionary with model data
            model_class: SQLAlchemy model class
        
        Returns:
            Model instance
        """
        return model_class(**data)
    
    @staticmethod
    def dict_to_pydantic(data: Dict[str, Any], pydantic_class: Type[M]) -> M:
        """
        Convert a dictionary to a Pydantic model instance
        
        Args:
            data: Dictionary with model data
            pydantic_class: Pydantic model class
        
        Returns:
            Pydantic model instance
        """
        return pydantic_class(**data)
    
    @staticmethod
    def pydantic_to_dict(model: BaseModel) -> Dict[str, Any]:
        """
        Convert a Pydantic model to a dictionary
        
        Args:
            model: Pydantic model instance
        
        Returns:
            Dictionary representation
        """
        return model.dict()
    
    @staticmethod
    def pydantic_to_model(pydantic_model: BaseModel, model_class: Type[T]) -> T:
        """
        Convert a Pydantic model to a SQLAlchemy model
        
        Args:
            pydantic_model: Pydantic model instance
            model_class: SQLAlchemy model class
        
        Returns:
            SQLAlchemy model instance
        """
        return model_class(**pydantic_model.dict())
    
    @staticmethod
    def update_model_from_dict(model: T, data: Dict[str, Any], exclude: Optional[List[str]] = None) -> T:
        """
        Update a SQLAlchemy model from a dictionary
        
        Args:
            model: SQLAlchemy model instance to update
            data: Dictionary with update data
            exclude: List of fields to exclude from update
        
        Returns:
            Updated model instance
        """
        if exclude is None:
            exclude = []
        
        for key, value in data.items():
            if key not in exclude and hasattr(model, key):
                setattr(model, key, value)
        
        return model