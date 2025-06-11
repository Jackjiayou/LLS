from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String, unique=True, nullable=False)
    session_key = Column(String)
    nickname = Column(String)
    avatar_url = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now()) 