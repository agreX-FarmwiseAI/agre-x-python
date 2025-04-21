from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List,Dict, Any
import datetime

from app.core.database import Base


# SQLAlchemy ORM model
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email_id = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    phone_number = Column(String(10))
    is_premium = Column(Boolean)
    active = Column(Boolean)
    created_on = Column(DateTime, default=func.now())
    
    # Relationships
    security_answer = relationship("UserSecAnswer", back_populates="user")


class UserSecAnswer(Base):
    __tablename__ = "user_security_answer"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    question_id = Column(Integer, ForeignKey("security_question.id"))
    answer = Column(Text, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="security_answer")
    question = relationship("SecurityQuestion")

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class SecurityQuestion(Base):
    __tablename__ = "security_question"
    
    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String(255), nullable=False)


# Pydantic models for API
class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime.datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class SecurityQuestionCreate(BaseModel):
    question_text: str


class SecurityQuestionResponse(BaseModel):
    id: int
    question_text: str
    
    class Config:
        from_attributes = True


class UserSecAnswerCreate(BaseModel):
    question_id: int
    answer: str


class UserSecAnswerResponse(BaseModel):
    id: int
    question: SecurityQuestionResponse
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

    class Config:
        from_attributes = True

class UserDetail(UserResponse):
    security_answers: List[UserSecAnswerResponse] = []
    
    class Config:
        from_attributes = True

class CustomData(BaseModel):
    email: EmailStr
    polygon_data: Dict[str, Any] = {}  # Replaces JSONObject
    polygon_data1: List[Dict[str, Any]] = []  # Replaces ArrayList<CustomData>

    class Config:
        from_attributes = True  # For ORM compatibility
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "polygon_data": {"key": "value"},
                "polygon_data1": [{"item": "value"}]
            }
        }
