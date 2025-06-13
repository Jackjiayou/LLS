from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Any, Optional

class DigitalHumanMessage(BaseModel):
    """数字人消息模型"""
    from_user: str  # 'user' 或 'digital_human'
    text: str
    voice_url: Optional[str] = None
    duration: Optional[str] = None
    timestamp: datetime
    video_url: Optional[str] = None

class DigitalHumanConversation(BaseModel):
    """数字人对话模型"""
    id: str
    user_id: str
    messages: List[DigitalHumanMessage]
    created_at: datetime
    updated_at: datetime

class DigitalHumanResponse(BaseModel):
    """数字人响应模型"""
    text: str
    voice_url: Optional[str] = None
    duration: Optional[str] = None
    video_url: Optional[str] = None

# 存储数字人对话的字典
digital_human_conversations = {} 