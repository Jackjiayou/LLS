# backend/app/schemas/practice.py

from pydantic import BaseModel,Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class StartPracticeRequest(BaseModel):
    sceneId: int
    userId: int

class StartPracticeResponse(BaseModel):
    practice_id: int
    started_at: datetime

class PracticeMessage(BaseModel):
    from_: str  # 使用 from_ 因为 from 是 Python 关键字
    text: str
    voiceUrl: Optional[str] = None
    duration: Optional[int] = None
    suggestion: Optional[str] = None
    timestamp: Optional[datetime] = None

    class Config:
        fields = {
            'from_': 'from'  # 在 JSON 中使用 'from' 而不是 'from_'
        }

class SavePracticeMessageRequest(BaseModel):
    practice_id: int
    message: PracticeMessage

class EndPracticeRequest(BaseModel):
    practice_id: int
    score_json: Optional[Dict[str, Any]] = None

class PracticeHistoryResponse(BaseModel):
    practice_id: int
    user_id: int
    scenario_id: int
    started_at: datetime
    ended_at: Optional[datetime]
    status: str
    score_json: Optional[Dict[str, Any]]
    messages: List[PracticeMessage]

# In backend/app/schemas/practice.py

class ChatMessage(BaseModel):
    from_: str = Field(alias='from')  # This tells Pydantic to accept 'from' in input
    text: str
    voiceUrl: Optional[str] = None
    duration: Optional[int] = 0
    suggestion: Optional[str] = None
    timestamp: str

    class Config:
        allow_population_by_field_name = True  # This allows both 'from' and 'from_' to work

class PracticeStatsResponse(BaseModel):
    practice_count: int
    total_duration: float  # 单位：小时
    scenario_count: int

class SaveJsonMessageRequest(BaseModel):
    practice_id: int
    chat_history: List[ChatMessage]