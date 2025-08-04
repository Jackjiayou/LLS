from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String(255), unique=True, index=True, nullable=False)
    session_key = Column(String(255), nullable=True)  # 微信session_key
    unionid = Column(String(255), unique=True, index=True, nullable=True)
    nickname = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)  # 新增：用户是否激活
    is_whitelisted = Column(Boolean, default=False)  # 新增：是否在白名单中
    is_admin = Column(Boolean, default=False)  # 新增：是否为管理员
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Whitelist(Base):
    """微信用户白名单表"""
    __tablename__ = "whitelist"
    
    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String(255), unique=True, index=True, nullable=False)
    unionid = Column(String(255), unique=True, index=True, nullable=True)
    nickname = Column(String(255), nullable=True)
    added_by = Column(String(255), nullable=True)  # 添加人
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)  # 是否激活

class AuthorizationRequest(Base):
    """申请授权表"""
    __tablename__ = "authorization_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String(255), index=True, nullable=False)
    unionid = Column(String(255), nullable=True)
    nickname = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)  # 申请理由
    status = Column(String(20), default="pending")  # pending, approved, rejected
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)  # 处理时间
    processed_by = Column(String(255), nullable=True)  # 处理人
    processed_reason = Column(Text, nullable=True)  # 处理理由 