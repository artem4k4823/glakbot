from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    discord_id: str = Field(..., min_length=3, max_length=64)
    username: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    is_admin: bool = False


class UserResponse(BaseModel):
    id: int
    discord_id: str
    username: str
    email: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True
