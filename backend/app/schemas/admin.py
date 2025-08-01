from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class AdminUserResponse(BaseModel):
    id: int
    openid: str
    nickname: Optional[str] = None
    is_admin: bool
    created_at: datetime

class AdminUserList(BaseModel):
    items: List[AdminUserResponse]
    total: int 