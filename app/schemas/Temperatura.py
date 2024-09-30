from sqlalchemy import Column, Integer, Float, DateTime
from app.db.database import Base
from datetime import datetime, timezone

class Temperature(Base):
    __tablename__ = "temperatura"
    
    id = Column(Integer, primary_key=True, index=True)
    value = Column(Float, nullable=False)  # Temperatura armazenada
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Usar GMT (UTC)
