from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Any

# --- Schémas pour Site ---
class SiteBase(BaseModel):
    name: str = Field(..., example="Siège Social Abidjan")
    address: Optional[str] = Field(None, example="Plateau, Avenue 123")
    timezone: str = Field("Africa/Abidjan", example="Africa/Abidjan")

class SiteCreate(SiteBase):
    organization_id: str

class SiteUpdate(SiteBase):
    name: Optional[str] = None
    address: Optional[str] = None
    timezone: Optional[str] = None

class Site(SiteBase):
    id: str
    organization_id: str

    class Config:
        from_attributes = True

# --- Schémas pour Organization ---
class OrganizationBase(BaseModel):
    name: str = Field(..., example="Tanga Group")
    description: Optional[str] = Field(None, example="Société de technologie")
    email: Optional[EmailStr] = Field(None, example="contact@tangagroup.com")
    phone: Optional[str] = Field(None, example="+225 0102030405")
    timezone: str = Field("Africa/Abidjan", example="Africa/Abidjan")
    plan: Optional[str] = Field("standard", example="premium")
    is_active: bool = Field(True)
    settings: Optional[dict[str, Any]] = Field({}, example={"notifications_enabled": True})

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    plan: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[dict[str, Any]] = None

class Organization(OrganizationBase):
    id: str
    sites: List[Site] = []

    class Config:
        from_attributes = True