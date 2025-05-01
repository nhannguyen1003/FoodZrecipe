# TODO: Define Pydantic models for user data validation
from pydantic import BaseModel, EmailStr, Field
from backend.models.user import UserRole
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., description="User's email address")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User's password, minimum 8 characters")
    role: Optional[UserRole] = Field(default=UserRole.REGULAR, description="User role (regular or admin)")

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class UserResponse(UserInDB):
    pass

class UserDetailResponse(UserResponse):
    recipes_count: int = 0

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[UserRole] = None
    exp: Optional[datetime] = None