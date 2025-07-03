from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid

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

class DigitalHumanFile(Base):
    """数字人文件模型"""
    __tablename__ = "digital_human_files"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    file_type = Column(String(20), nullable=False)  # image, video, audio
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    upload_time = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    digital_humans = relationship("DigitalHuman", back_populates="image_file", foreign_keys="DigitalHuman.image_file_id")
    video_digital_humans = relationship("DigitalHuman", back_populates="video_file", foreign_keys="DigitalHuman.video_file_id")
    audio_digital_humans = relationship("DigitalHuman", back_populates="audio_file", foreign_keys="DigitalHuman.audio_file_id")

class DigitalHuman(Base):
    """数字人模型"""
    __tablename__ = "digital_humans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    image_file_id = Column(String(36), ForeignKey("digital_human_files.id"), nullable=True)
    video_file_id = Column(String(36), ForeignKey("digital_human_files.id"), nullable=True)
    audio_file_id = Column(String(36), ForeignKey("digital_human_files.id"), nullable=True)
    generate_video_path = Column(String(100), nullable=True)
    text_content = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="processing")  # processing, completed, failed
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    image_file = relationship("DigitalHumanFile", foreign_keys=[image_file_id], back_populates="digital_humans")
    video_file = relationship("DigitalHumanFile", foreign_keys=[video_file_id], back_populates="video_digital_humans")
    audio_file = relationship("DigitalHumanFile", foreign_keys=[audio_file_id], back_populates="audio_digital_humans") 