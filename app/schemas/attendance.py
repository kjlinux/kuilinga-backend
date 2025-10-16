from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any
from app.models.attendance import AttendanceType

# Schéma pour les informations de base sur l'employé dans la liste des présences
class AttendanceEmployee(BaseModel):
    id: str
    first_name: str
    last_name: str
    employee_number: Optional[str] = None

    class Config:
        from_attributes = True

# Schéma pour les informations de base sur le département
class AttendanceDepartment(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True

# Schéma pour les informations de base sur le site
class AttendanceSite(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True

# Schéma pour les informations de base sur le dispositif
class AttendanceDevice(BaseModel):
    id: str
    serial_number: str
    type: str

    class Config:
        from_attributes = True

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

# Propriétés pour la mise à jour d'un pointage
class AttendanceUpdate(BaseModel):
    timestamp: Optional[datetime] = None
    type: Optional[AttendanceType] = None
    geo: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = None

# Schéma principal pour retourner un pointage via l'API
class Attendance(AttendanceBase):
    id: str
    duration: Optional[str] = None  # ex: "8h 30m"
    employee: Optional[AttendanceEmployee] = None
    device: Optional[AttendanceDevice] = None

    class Config:
        from_attributes = True