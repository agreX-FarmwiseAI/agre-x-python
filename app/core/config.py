import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # API configuration
    API_VERSION: str = "1.0.0"
    VERSION: str = "1.0.0"
    PROJECT_NAME: str = "AgReX API"
    
    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+mysqlconnector://admin:AllIsWell!@tnau-dev.c5uedrzo7co7.ap-south-1.rds.amazonaws.com/agrex_prod")
    
    # Security configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS configuration
    CORS_ORIGINS: str = "*"
    
    # File upload configuration
    UPLOAD_FOLDER: str = "uploads"
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    
    # Python service configuration
    PYTHON_EXECUTABLE: str = "python"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()