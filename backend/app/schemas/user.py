from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LoginRequest(BaseModel):
    code: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None

class UserBase(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    openid: str
    session_key: str

class User(UserBase):
    id: int
    openid: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime 