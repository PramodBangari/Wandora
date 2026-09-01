from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime

from app.core.database import Base

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(160), nullable=False)
    description = Column(String(1000), default="")
    category = Column(String(50), nullable=False)
    location_name = Column(String(160), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    start_time = Column(String(80), nullable=False)
    joined = Column(Integer, default=0)
    max_participants = Column(Integer, default=10)
    host = Column(String(100), default="Wandora user")
    created_at = Column(DateTime, default=datetime.utcnow)
