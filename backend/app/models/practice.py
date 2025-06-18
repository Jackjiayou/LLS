# backend/app/models/practice.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class PracticeScenario(Base):
    __tablename__ = "practice_scenarios"

    scenario_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    goal = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    # 添加关系
    practices = relationship("PracticeRecord", back_populates="scenario")

class PracticeRecord(Base):
    __tablename__ = "practice_records"

    practice_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("practice_scenarios.scenario_id"), nullable=False)
    started_at = Column(DateTime, nullable=False, server_default=func.now())
    ended_at = Column(DateTime)
    status = Column(String(20), nullable=False, server_default='in_progress')
    score_json = Column(JSON)
    chat_history = Column(JSON, nullable=False, server_default='[]')  # 添加这行
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # 添加关系
    scenario = relationship("PracticeScenario", back_populates="practices")
    messages = relationship("PracticeMessage", back_populates="practice")

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

    # 添加关系
    practice = relationship("PracticeRecord", back_populates="messages")