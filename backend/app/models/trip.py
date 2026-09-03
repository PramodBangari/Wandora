from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.core.database import Base

class Trip(Base):
    __tablename__ = 'trips'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    destination = Column(String(160), nullable=False)
    start_date = Column(String(40), nullable=False)
    end_date = Column(String(40), nullable=False)
    description = Column(String(1000), default='')
    created_at = Column(DateTime, default=datetime.utcnow)
