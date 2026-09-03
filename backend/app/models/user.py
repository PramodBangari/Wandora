from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(40), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    google_sub = Column(String(255), unique=True, index=True, nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    verification_code_hash = Column(String(255), nullable=True)
    verification_expires_at = Column(DateTime, nullable=True)
    reset_code_hash = Column(String(255), nullable=True)
    reset_expires_at = Column(DateTime, nullable=True)
    bio = Column(Text, default="")
    interests = Column(String(500), default="")
    city = Column(String(100), default="Bengaluru")
    avatar_url = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
