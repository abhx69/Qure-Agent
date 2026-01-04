"""
models.py - SQLAlchemy models
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(100))
    created_at = Column(DateTime, default=func.now())

class UserConnection(Base):
    __tablename__ = 'user_connections'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    provider = Column(Enum('google', 'asana'), nullable=False)
    provider_user_id = Column(String(255))
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    expires_at = Column(DateTime)
    metadata = Column(JSON)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class AgentChatLog(Base):
    __tablename__ = 'agent_chat_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(Enum('user', 'assistant'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())

class AIPendingAction(Base):
    __tablename__ = 'ai_pending_actions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    provider = Column(Enum('google', 'asana'))
    action_type = Column(String(50))
    draft_payload = Column(JSON)
    status = Column(
        Enum('pending', 'approved', 'rejected', 'executed'),
        default='pending'
    )
    created_at = Column(DateTime, default=func.now())
    executed_at = Column(DateTime)