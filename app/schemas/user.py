"""
Pydantic schemas for user authentication
"""
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=6, max_length=100)
    birthday: date = Field(..., description="User birth date (YYYY-MM-DD)")


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class User(UserBase):
    """Schema for user response"""
    id: str
    birthday: date | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserMeUpdate(BaseModel):
    """Schema for updating current user's profile"""
    birthday: date = Field(..., description="User birth date (YYYY-MM-DD)")


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Schema for authentication response (register/login with user data)"""
    user: User
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded JWT token data"""
    user_id: str | None = None
