from pydantic import BaseModel
from datetime import datetime

class TemperatureCreate(BaseModel):
    value: float

class Temperature(BaseModel):
    id: int
    value: float
    timestamp: datetime

    class Config:
        from_attributes = True
