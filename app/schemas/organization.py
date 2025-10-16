from pydantic import BaseModel, Field
from typing import Optional, Any

# Schéma de base pour l'organisation
class OrganizationBase(BaseModel):
    name: str = Field(..., example="Tanga Group")
    description: Optional[str] = Field(None, example="Société de technologie")
    email: Optional[str] = Field(None, example="contact@tangagroup.com")
    phone: Optional[str] = Field(None, example="+225 0102030405")
    timezone: str = Field("Africa/Abidjan", example="Africa/Abidjan")
    plan: Optional[str] = Field("standard", example="premium")
    is_active: bool = True

# Schéma pour la création d'une organisation
class OrganizationCreate(OrganizationBase):
    pass

# Schéma pour la mise à jour d'une organisation
class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    plan: Optional[str] = None
    is_active: Optional[bool] = None

# Schéma complet pour retourner via l'API
class Organization(OrganizationBase):
    id: str
    sites_count: int = 0
    employees_count: int = 0
    users_count: int = 0

    class Config:
        from_attributes = True