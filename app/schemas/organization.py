from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List, Any

# Schéma de base pour Site
class SiteBase(BaseModel):
    name: str = Field(..., example="Siège Social")
    address: Optional[str] = Field(None, example="123 Rue de la République")
    timezone: str = Field("UTC", example="Europe/Paris")

class SiteCreate(SiteBase):
    organization_id: UUID

class SiteUpdate(SiteBase):
    name: Optional[str] = None
    address: Optional[str] = None
    timezone: Optional[str] = None

class Site(SiteBase):
    id: UUID
    organization_id: UUID

    class Config:
        from_attributes = True

# Schéma de base pour Organization
class OrganizationBase(BaseModel):
    name: str = Field(..., example="Ma Grande Entreprise")
    plan: Optional[str] = Field(None, example="premium")
    settings: Optional[dict[str, Any]] = Field(None, example={"theme": "dark"})

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(OrganizationBase):
    name: Optional[str] = None
    plan: Optional[str] = None
    settings: Optional[dict[str, Any]] = None

class Organization(OrganizationBase):
    id: UUID
    sites: List[Site] = []

    class Config:
        from_attributes = True