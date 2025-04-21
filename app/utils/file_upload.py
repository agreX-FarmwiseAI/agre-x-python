import os
import uuid
import shutil
from fastapi import UploadFile
from typing import Optional, List, Tuple
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class FileUpload:
    """
    Utility class for file upload operations
    """
    @staticmethod
    def get_file_path(user_id: int, file_prefix: str, filename: str) -> str:
        """
        Generate a file path for an uploaded file
        
        Args:
            user_id: User ID
            file_prefix: Prefix for the file (e.g., 'data_product', 'model')
            filename: Original filename
        
        Returns:
            Path where the file should be stored
        """
        # Create directory if it doesn't exist
        upload_dir = os.path.join(settings.UPLOAD_FOLDER, f"user_{user_id}")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename to avoid collisions
        file_uuid = str(uuid.uuid4())
        file_extension = os.path.splitext(filename)[1].lower()
        safe_filename = f"{file_prefix}_{file_uuid}{file_extension}"
        
        return os.path.join(upload_dir, safe_filename)
    
    @staticmethod
    async def save_upload_file(upload_file: UploadFile, destination: str) -> Tuple[bool, Optional[str]]:
        """
        Save an uploaded file to the specified destination
        
        Args:
            upload_file: The uploaded file
            destination: Where to save the file
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            with open(destination, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
            
            return True, None
        
        except Exception as e:
            error_msg = f"Error saving file: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def get_file_size(file_path: str) -> Optional[float]:
        """
        Get the size of a file in bytes
        
        Args:
            file_path: Path to the file
        
        Returns:
            File size in bytes or None if file doesn't exist
        """
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"Error getting file size: {str(e)}")
            return None
    
    @staticmethod
    def delete_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a file
        
        Args:
            file_path: Path to the file
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                return True, None
            else:
                return False, "File doesn't exist"
        
        except Exception as e:
            error_msg = f"Error deleting file: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def is_allowed_file(filename: str, allowed_extensions: List[str]) -> bool:
        """
        Check if a file has an allowed extension
        
        Args:
            filename: Name of the file
            allowed_extensions: List of allowed extensions (e.g., ['.jpg', '.png'])
        
        Returns:
            True if file has an allowed extension, False otherwise
        """
        return os.path.splitext(filename)[1].lower() in allowed_extensions