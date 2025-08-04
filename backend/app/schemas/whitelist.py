from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class WhitelistCreate(BaseModel):
    openid: str
    unionid: Optional[str] = None
    nickname: Optional[str] = None

class WhitelistResponse(BaseModel):
    id: int
    openid: str
    unionid: Optional[str] = None
    nickname: Optional[str] = None
    added_at: datetime
    is_active: bool

class WhitelistList(BaseModel):
    items: List[WhitelistResponse]
    total: int

class AuthorizationRequestCreate(BaseModel):
    openid: str
    unionid: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    reason: Optional[str] = None

class AuthorizationRequestResponse(BaseModel):
    id: int
    openid: str
    unionid: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    reason: Optional[str] = None
    status: str
    requested_at: datetime
    processed_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    processed_reason: Optional[str] = None

class AuthorizationRequestList(BaseModel):
    items: List[AuthorizationRequestResponse]
    total: int

class AuthorizationRequestProcess(BaseModel):
    status: str  # approved, rejected
    reason: Optional[str] = None 