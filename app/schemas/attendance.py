from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Any
from app.models.attendance import AttendanceType

# Schéma de base pour les pointages
class AttendanceBase(BaseModel):
    timestamp: datetime = Field(..., example=datetime.now())
    type: AttendanceType = Field(..., example=AttendanceType.IN)
    geo: Optional[str] = Field(None, example="48.8584,2.2945")
    metadata: Optional[dict[str, Any]] = Field(None)

    class Config:
        from_attributes = True

# Schéma pour la création d'un pointage
class AttendanceCreate(AttendanceBase):
    employee_id: UUID
    device_id: Optional[UUID] = None

# Schéma pour la mise à jour d'un pointage (généralement non utilisé, mais possible)
class AttendanceUpdate(BaseModel):
    timestamp: Optional[datetime] = None
    type: Optional[AttendanceType] = None
    geo: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

# Schéma pour la lecture des données d'un pointage
class Attendance(AttendanceBase):
    id: UUID
    employee_id: UUID
    device_id: Optional[UUID] = None