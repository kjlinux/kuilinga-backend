from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any
from app.models.attendance import AttendanceType

# Schéma pour les informations de base sur l'employé dans la liste des présences
class AttendanceEmployee(BaseModel):
    id: str = Field(..., description="Identifiant unique de l'employé")
    first_name: str = Field(..., description="Prénom de l'employé")
    last_name: str = Field(..., description="Nom de famille de l'employé")
    employee_number: Optional[str] = Field(None, description="Matricule de l'employé")

    class Config:
        from_attributes = True

# Schéma pour les informations de base sur le département
class AttendanceDepartment(BaseModel):
    id: str = Field(..., description="Identifiant unique du département")
    name: str = Field(..., description="Nom du département")

    class Config:
        from_attributes = True

# Schéma pour les informations de base sur le site
class AttendanceSite(BaseModel):
    id: str = Field(..., description="Identifiant unique du site")
    name: str = Field(..., description="Nom du site")

    class Config:
        from_attributes = True

# Schéma pour les informations de base sur le dispositif
class AttendanceDevice(BaseModel):
    id: str = Field(..., description="Identifiant unique du terminal")
    serial_number: str = Field(..., description="Numéro de série du terminal")
    type: str = Field(..., description="Type de terminal")

    class Config:
        from_attributes = True

# Propriétés partagées pour les pointages
class AttendanceBase(BaseModel):
    timestamp: datetime = Field(..., example=datetime.now(), description="Date et heure du pointage (format ISO 8601)")
    type: AttendanceType = Field(..., example=AttendanceType.IN, description="Type de pointage : 'in' (entrée) ou 'out' (sortie)")
    geo: Optional[str] = Field(None, example="5.3346, -4.0022", description="Coordonnées GPS au format 'latitude, longitude'")
    extra_data: Optional[dict[str, Any]] = Field({}, example={"source": "mobile_app"}, description="Données supplémentaires (source, metadata)")

# Propriétés pour la création d'un pointage
class AttendanceCreate(AttendanceBase):
    employee_id: str = Field(..., description="ID de l'employé qui pointe")
    device_id: Optional[str] = Field(None, description="ID du terminal de pointage utilisé")

# Propriétés pour la mise à jour d'un pointage
class AttendanceUpdate(BaseModel):
    timestamp: Optional[datetime] = Field(None, description="Date et heure du pointage")
    type: Optional[AttendanceType] = Field(None, description="Type de pointage")
    geo: Optional[str] = Field(None, description="Coordonnées GPS")
    extra_data: Optional[dict[str, Any]] = Field(None, description="Données supplémentaires")

# Schéma principal pour retourner un pointage via l'API
class Attendance(AttendanceBase):
    id: str = Field(..., description="Identifiant unique du pointage")
    duration: Optional[str] = Field(None, description="Durée calculée depuis le dernier pointage (ex: '8h 30m')")
    employee: Optional[AttendanceEmployee] = Field(None, description="Employé concerné par le pointage")
    device: Optional[AttendanceDevice] = Field(None, description="Terminal utilisé pour le pointage")

    class Config:
        from_attributes = True