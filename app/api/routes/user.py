from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List, Any
from app.core.database import get_db
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    get_current_active_user, get_current_user
)
from app.models.user import (
    User, UserCreate, UserResponse, UserLogin, 
    Token, SecurityQuestion, SecurityQuestionCreate,
    SecurityQuestionResponse, UserSecAnswer, UserSecAnswerCreate,
    UserSecAnswerResponse, UserDetail, LoginRequest
)
from app.core.exceptions import ResourceNotFoundException
from app.services.user import UserService
import logging

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    return await UserService.create_user(db=db, user=user)

@router.get("/", response_model=List[UserResponse])
async def get_users(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """Get all users"""
    return await UserService.get_users(db=db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    return await UserService.get_user(db=db, user_id=user_id)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    first_name: str = None,
    last_name: str = None,
    email: str = None,
    db: Session = Depends(get_db)
):
    """Update user information"""
    return await UserService.update_user(
        db=db,
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        email=email
    )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user"""
    await UserService.delete_user(db=db, user_id=user_id)
    return None

@router.post("/createQuestions", response_model=SecurityQuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_security_question(
    question: SecurityQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new security question
    """
    db_question = SecurityQuestion(question_text=question.question_text)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


@router.get("/getQuestions", response_model=List[SecurityQuestionResponse])
async def get_security_questions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all security questions
    """
    questions = db.query(SecurityQuestion).offset(skip).limit(limit).all()
    return questions


@router.post("/CreateAnswer", response_model=UserSecAnswerResponse, status_code=status.HTTP_201_CREATED)
async def create_security_answer(
    answer: UserSecAnswerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a security question answer for the current user
    """
    # Check if question exists
    question = db.query(SecurityQuestion).filter(SecurityQuestion.id == answer.question_id).first()
    if not question:
        raise ResourceNotFoundException("SecurityQuestion", answer.question_id)
    
    # Create answer
    db_answer = UserSecAnswer(
        user_id=current_user.id,
        question_id=answer.question_id,
        answer=answer.answer
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    
    # Return with question data
    result = UserSecAnswerResponse(
        id=db_answer.id,
        question=SecurityQuestionResponse(
            id=question.id,
            question_text=question.question_text
        )
    )
    return result

@router.post("/login")
def login(login_request: LoginRequest, db: Session = Depends(get_db), response_model=List[UserResponse]):
    """User login"""
    user = db.query(User).filter(User.email_id == login_request.email).first()
    logging.info(f"User details: {user}") 
    if user:
        if user.password == login_request.password:
            return user
    return []

@router.post("/polygon")
async def polygon(poly_data: List[List[Any]] = Body(...)):
    """Process polygon data"""
    return await UserService.polygon_data(data = poly_data)
    #return "Polygon data processed"

