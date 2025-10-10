from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any
from .user import User

# Propriétés partagées pour les employés
class EmployeeBase(BaseModel):
    first_name: str = Field(..., example="Kouassi")
    last_name: str = Field(..., example="Jean")
    email: EmailStr = Field(..., example="kouassi.jean@example.com")
    phone: Optional[str] = Field(None, example="+2250102030405")
    employee_number: Optional[str] = Field(None, example="EMP001")
    department: Optional[str] = Field(None, example="Technologie")
    position: Optional[str] = Field(None, example="Développeur Backend")
    badge_id: Optional[str] = Field(None, example="BADGE-KJ-001")
    metadata: Optional[dict[str, Any]] = Field({}, example={"skill": "Python"})

# Propriétés pour la création d'un employé
class EmployeeCreate(EmployeeBase):
    organization_id: str
    site_id: Optional[str] = None
    user_id: Optional[str] = None

# Propriétés pour la mise à jour d'un employé
class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    employee_number: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    badge_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    site_id: Optional[str] = None
    user_id: Optional[str] = None

# Propriétés à retourner via l'API
class Employee(EmployeeBase):
    id: str
    organization_id: str
    site_id: Optional[str] = None
    user: Optional[User] = None

    class Config:
        from_attributes = True