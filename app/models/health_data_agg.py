from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.sql import func
from app.database import Base

class HealthDataAgg(Base):
    __tablename__ = "health_data_agg"

    id = Column(Integer, primary_key=True)

    device_id = Column(Integer, ForeignKey("devices.id"))

    avg_hr = Column(Float)
    avg_spo2 = Column(Float)
    avg_temp = Column(Float)

    avg_humidity = Column(Float)

    bucket = Column(String(20))   # minute / hour

    bucket_time = Column(DateTime)

    created_at = Column(DateTime(timezone=True), server_default=func.now())