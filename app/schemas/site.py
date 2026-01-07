from pydantic import BaseModel, Field
from typing import Optional
from .organization import OrganizationBase

class SiteOrganization(OrganizationBase):
    id: str = Field(..., description="Identifiant unique de l'organisation")
    name: str = Field(..., description="Nom de l'organisation")

    class Config:
        from_attributes = True

class SiteBase(BaseModel):
    name: str = Field(..., example="Siège Social Abidjan", description="Nom du site")
    address: Optional[str] = Field(None, example="Plateau, Avenue 123", description="Adresse physique du site")
    timezone: str = Field("Africa/Abidjan", example="Africa/Abidjan", description="Fuseau horaire du site")

class SiteCreate(SiteBase):
    organization_id: str = Field(..., description="ID de l'organisation propriétaire")

class SiteUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Nom du site")
    address: Optional[str] = Field(None, description="Adresse physique du site")
    timezone: Optional[str] = Field(None, description="Fuseau horaire du site")

class Site(SiteBase):
    id: str = Field(..., description="Identifiant unique du site")
    organization: Optional[SiteOrganization] = Field(None, description="Organisation propriétaire")
    departments_count: int = Field(0, description="Nombre de départements dans le site")
    employees_count: int = Field(0, description="Nombre d'employés sur le site")
    devices_count: int = Field(0, description="Nombre de terminaux sur le site")

    class Config:
        from_attributes = True