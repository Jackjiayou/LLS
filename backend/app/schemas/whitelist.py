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