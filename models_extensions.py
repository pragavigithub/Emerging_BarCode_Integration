from app import db
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime

class Branch(db.Model):
    """Branch/Location model for multi-branch support"""
    __tablename__ = 'branches'
    
    id = Column(String(10), primary_key=True)  # Branch code like 'BR001'
    name = Column(String(100), nullable=False)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    manager_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # Default branch for new users
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserSession(db.Model):
    """Track user login sessions"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = Column(String(256), nullable=False)
    branch_id = Column(String(10), nullable=True)
    login_time = Column(DateTime, default=datetime.utcnow)
    logout_time = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

class PasswordResetToken(db.Model):
    """Password reset tokens for users"""
    __tablename__ = 'password_reset_tokens'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, db.ForeignKey('users.id'), nullable=False)
    token = Column(String(256), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_by = Column(Integer, db.ForeignKey('users.id'), nullable=True)  # Admin who created token
    created_at = Column(DateTime, default=datetime.utcnow)