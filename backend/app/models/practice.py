# backend/app/models/practice.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class PracticeScenario(Base):
    __tablename__ = "practice_scenarios"

    scenario_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    goal = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    # 暂时注释掉关系定义，避免初始化错误
    # practices = relationship("PracticeRecord", back_populates="scenario", 
    #                        primaryjoin="PracticeScenario.scenario_id == PracticeRecord.scenario_id")

class PracticeRecord(Base):
    __tablename__ = "practice_records"

    practice_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    scenario_id = Column(Integer, nullable=False)
    status = Column(String(50), default='in_progress')
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    chat_history = Column(JSON)
    score_json = Column(JSON)  # 保留原有字段，用于兼容
    conversation_id = Column(String(255))
    is_deleted = Column(Integer, nullable=False, server_default='0')
    
    # 新增三个独立字段
    organization_score = Column(JSON)  # 语言组织能力分数和分析
    persuasiveness_score = Column(JSON)  # 说服力分数和分析
    fluency_pronunciation_expression_score = Column(JSON)  # 流利度、发音、表达分数和分析

    # 暂时注释掉关系定义，避免初始化错误
    # scenario = relationship("PracticeScenario", back_populates="practices",
    #                       primaryjoin="PracticeRecord.scenario_id == PracticeScenario.scenario_id")
    # messages = relationship("PracticeMessage", back_populates="practice")

class PracticeMessage(Base):
    __tablename__ = "practice_messages"

    message_id = Column(Integer, primary_key=True, index=True)
    practice_id = Column(Integer, ForeignKey("practice_records.practice_id"), nullable=False)
    message_type = Column(String(10), nullable=False)  # 'user' or 'robot'
    content = Column(Text, nullable=False)
    voice_url = Column(Text)
    duration = Column(Integer)
    suggestion = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    message_order = Column(Integer, nullable=False)

    # 暂时注释掉关系定义，避免初始化错误
    # practice = relationship("PracticeRecord", back_populates="messages")