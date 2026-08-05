from fastapi import APIRouter, Depends, HTTPException, status, Response
import uuid
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import get_db
from app.models.user import User
from app.services.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str = "Web User"
    phone_number: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Message(BaseModel):
    message: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str

@router.post("/register", response_model=Message)
def register(user_data: UserCreate, response: Response, db: Session = Depends(get_db)):
    # Check if email exists
    stmt = select(User).where(User.email == user_data.email)
    existing_email = db.execute(stmt).scalar_one_or_none()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Check if phone exists
    stmt = select(User).where(User.phone_number == user_data.phone_number)
    existing_phone = db.execute(stmt).scalar_one_or_none()
    if existing_phone:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    user = User(
        email=user_data.email,
        phone_number=user_data.phone_number,
        name=user_data.name,
        password_hash=hash_password(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id))
    csrf_token = uuid.uuid4().hex
    response.set_cookie(key="access_token", value=token, httponly=True, secure=True, samesite="strict")
    response.set_cookie(key="csrf_token", value=csrf_token, httponly=False, secure=True, samesite="strict")
    return {"message": "Registered successfully"}

@router.post("/login", response_model=Message)
def login(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    stmt = select(User).where(User.email == user_data.email)
    user = db.execute(stmt).scalar_one_or_none()
    
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(str(user.id))
    csrf_token = uuid.uuid4().hex
    response.set_cookie(key="access_token", value=token, httponly=True, secure=True, samesite="strict")
    response.set_cookie(key="csrf_token", value=csrf_token, httponly=False, secure=True, samesite="strict")
    return {"message": "Logged in successfully"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name
    }

@router.post("/logout", response_model=Message)
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("csrf_token")
    return {"message": "Logged out successfully"}
