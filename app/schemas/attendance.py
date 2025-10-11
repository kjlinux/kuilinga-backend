from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any
from app.models.attendance import AttendanceType

# Propriétés partagées pour les pointages
class AttendanceBase(BaseModel):
    timestamp: datetime = Field(..., example=datetime.now())
    type: AttendanceType = Field(..., example=AttendanceType.IN)
    geo: Optional[str] = Field(None, example="5.3346, -4.0022") # Lat, Lon
    extra_data: Optional[dict[str, Any]] = Field({}, example={"source": "mobile_app"})

# Propriétés pour la création d'un pointage
class AttendanceCreate(AttendanceBase):
    employee_id: str
    device_id: Optional[str] = None

# Propriétés pour la mise à jour d'un pointage (rarement utilisé)
class AttendanceUpdate(BaseModel):
    timestamp: Optional[datetime] = None
    type: Optional[AttendanceType] = None
    geo: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = None

# Propriétés à retourner via l'API
class Attendance(AttendanceBase):
    id: str
    employee_id: str
    device_id: Optional[str] = None

    class Config:
        from_attributes = True
