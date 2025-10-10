from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Optional, Any
from .user import User

# Schéma de base pour les employés
class EmployeeBase(BaseModel):
    name: str = Field(..., example="John Doe")
    email: Optional[EmailStr] = Field(None, example="johndoe@work.com")
    badge_id: Optional[str] = Field(None, unique=True, index=True, example="EMP-12345")
    metadata: Optional[dict[str, Any]] = Field(None)

    class Config:
        from_attributes = True

# Schéma pour la création d'un employé
class EmployeeCreate(EmployeeBase):
    organization_id: UUID
    site_id: Optional[UUID] = None
    user_id: Optional[UUID] = None

# Schéma pour la mise à jour d'un employé
class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    badge_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    site_id: Optional[UUID] = None

# Schéma pour la lecture des données d'un employé
class Employee(EmployeeBase):
    id: UUID
    organization_id: UUID
    site_id: Optional[UUID] = None
    user: Optional[User] = None