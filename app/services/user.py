import json
import os
import random
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from typing import List, Optional
from datetime import datetime
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from app.models.user import (
    User, UserCreate, SecurityQuestion, SecurityQuestionCreate,UserLogin,
    UserSecAnswer, UserSecAnswerCreate, CustomData
)

from app.core.config import settings
from app.core.exceptions import ResourceNotFoundException
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from app.models.user import User, UserCreate
#from app.core.security import get_password_hash, create_access_token
from app.core.config import settings
from app.core.exceptions import ResourceNotFoundException

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    async def get_all_users(db: Session) -> List[User]:
        """Get all users"""
        return db.query(User).all()

    @staticmethod
    async def add_user(db: Session, user: UserCreate) -> int:
        """Add a new user"""
        # Validate email
        if db.query(User).filter(User.email == user.email).first():
            raise HTTPException(status_code=400, detail="e01")  # Email exists

        # Validate license code
        if db.query(User).filter(User.lic_code == user.lic_code).first():
            raise HTTPException(status_code=400, detail="e02")  # License code exists

        db_user = User(
            username=user.username,
            email=user.email,
            password=user.password,  # In production, this should be hashed
            first_name=user.first_name,
            last_name=user.last_name,
            lic_code=user.lic_code
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user.id

    @staticmethod
    async def get_email_list(db: Session) -> List[str]:
        """Get list of all emails"""
        return [user.email for user in db.query(User).all()]

    @staticmethod
    async def get_lic_codes(db: Session) -> List[str]:
        """Get list of all license codes"""
        return [user.lic_code for user in db.query(User).all()]

    @staticmethod
    async def get_all_questions(db: Session) -> List[SecurityQuestion]:
        """Get all security questions"""
        return db.query(SecurityQuestion).all()

    @staticmethod
    async def login(db: Session, user: UserLogin) -> List[User]:
        """Login user"""
        db_user = db.query(User).filter(
            User.email == user.email,
            User.password == user.password  # In production, use proper password verification
        ).all()
        return db_user if db_user else []

    @staticmethod
    async def send_email(data: CustomData) -> bool:
        """Send email"""
        try:
            # Configure your email settings here
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = "your-email@gmail.com"
            sender_password = "your-app-password"

            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = data.email
            msg["Subject"] = data.subject or "No Subject"

            msg.attach(MIMEText(data.message or "", "plain"))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

            return True
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    @staticmethod
    async def polygon_data(data: List[List[float]]) -> str:
        """Process polygon data and save as GeoJSON file
        
        Args:
            data: A 2D list of coordinates representing a polygon
            
        Returns:
            str: Path to the generated GeoJSON file
        """
        feature_collection = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": data
                },
                "properties": {}
            }]
        }

        random_number = random.random()
        base_path = "/home/ubuntu/AgriX-Api/AgriXApi-Release/GeoJson/"
        filename = f"polygon_{random_number}.Geojson"
        filepath = os.path.join(base_path, filename)

        try:
            # Create directory if it doesn't exist
            os.makedirs(base_path, exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(feature_collection, f)
                
            return filepath
            
        except IOError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error writing GeoJSON file: {str(e)}"
            )

    