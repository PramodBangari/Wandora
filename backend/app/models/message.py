from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.core.database import Base

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey('activities.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    text = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
