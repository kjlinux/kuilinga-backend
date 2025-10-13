from pydantic import BaseModel, Field
from typing import Optional, Any, List
from .site import Site

# Schéma pour l'organisation
class OrganizationBase(BaseModel):
    name: str = Field(..., example="Tanga Group")
    industry: Optional[str] = Field(None, example="Société de technologie")
    contact_email: Optional[str] = Field(None, example="contact@tangagroup.com")
    phone_number: Optional[str] = Field(None, example="+225 0102030405")
    timezone: str = Field("Africa/Abidjan", example="Africa/Abidjan")
    subscription_plan: str = Field("standard", example="premium")
    is_active: bool = True
    settings: Optional[dict[str, Any]] = Field({}, example={"enable_geo_fencing": False})

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    contact_email: Optional[str] = None
    phone_number: Optional[str] = None
    timezone: Optional[str] = None
    subscription_plan: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[dict[str, Any]] = None

class Organization(OrganizationBase):
    id: str
    sites: List[Site] = []

    class Config:
        from_attributes = True
