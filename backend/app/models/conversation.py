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

# 存储对话的字典
conversations = {}

# 改进建议模板
suggestion_templates = [
    "您的表达可以更加简洁明了，建议减少重复词语，直接表达核心信息。",
    "可以使用更专业的术语来增强可信度，比如将'很好的产品'改为'高性价比的解决方案'。",
    "回答时可以加入一些数据支持，增强说服力，例如'我们的产品已帮助超过1000家企业提升了30%的效率'。",
    "语速过快，建议适当放慢并在关键点停顿，让客户有时间消化信息。",
    "可以先认同客户的顾虑，再提出解决方案，如'您提到的价格问题很重要，我们可以...'。"
] 