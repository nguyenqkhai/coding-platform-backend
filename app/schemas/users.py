from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Base user schema for shared properties
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    rating: int = 0

# Schema for creating a user
class UserCreate(UserBase):
    password: str

# Schema for updating a user
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    rating: Optional[int] = None
    password: Optional[str] = None

# Schema for returning user data
class UserResponse(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        orm_mode = True

# Schema for token
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema for token data
class TokenData(BaseModel):
    username: Optional[str] = None