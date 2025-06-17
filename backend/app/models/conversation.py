from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class Message(BaseModel):
    from_user: str  # 'user' 或 'robot'
    text: str
    voiceUrl: str
    duration: str
    timestamp: datetime
    suggestion: Optional[str] = None

class Conversation(BaseModel):
    id: str
    user_id: str
    scene_id: int
    messages: List[Message]
    created_at: datetime
    updated_at: datetime

class ConversationCreate(BaseModel):
    user_id: str
    scene_id: int

class ConversationUpdate(BaseModel):
    messages: List[Message]

