from pydantic import BaseModel, Field
from typing import Optional, Any
from .department import Department

# Propriétés partagées pour les employés
class EmployeeBase(BaseModel):
    last_name: str = Field(..., example="Kouassi")
    first_name: str = Field(..., example="Jean")
    email: str = Field(..., example="kouassi.jean@example.com")
    phone_number: Optional[str] = Field(None, example="+2250102030405")
    employee_id: Optional[str] = Field(None, example="EMP001")
    position: Optional[str] = Field(None, example="Développeur Backend")
    badge_number: Optional[str] = Field(None, example="BADGE-KJ-001")
    extra_data: Optional[dict[str, Any]] = Field({}, example={"is_remote": True})

# Propriétés pour la création d'un employé
class EmployeeCreate(EmployeeBase):
    organization_id: str
    department_id: Optional[str] = None
    user_id: Optional[str] = None

# Propriétés pour la mise à jour d'un employé
class EmployeeUpdate(BaseModel):
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    employee_id: Optional[str] = None
    department_id: Optional[str] = None
    position: Optional[str] = None
    badge_number: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = None

# Propriétés à retourner via l'API
class Employee(EmployeeBase):
    id: str
    organization_id: str
    user_id: Optional[str] = None
    department: Optional[Department] = None

    class Config:
        from_attributes = True
