from pydantic import BaseModel, Field
from typing import Optional
from .organization import OrganizationBase

class SiteOrganization(OrganizationBase):
    id: str
    name: str

    class Config:
        from_attributes = True

class SiteBase(BaseModel):
    name: str = Field(..., example="Siège Social Abidjan")
    address: Optional[str] = Field(None, example="Plateau, Avenue 123")
    timezone: str = Field("Africa/Abidjan", example="Africa/Abidjan")

class SiteCreate(SiteBase):
    organization_id: str

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    timezone: Optional[str] = None

class Site(SiteBase):
    id: str
    organization: Optional[SiteOrganization] = None
    departments_count: int = 0
    employees_count: int = 0
    devices_count: int = 0

    class Config:
        from_attributes = True