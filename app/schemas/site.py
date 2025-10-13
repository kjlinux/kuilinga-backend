from pydantic import BaseModel, Field
from typing import Optional

class SiteBase(BaseModel):
    name: str = Field(..., example="Siège Social Abidjan")
    location: Optional[str] = Field(None, example="Plateau, Avenue 123")
    timezone: str = Field("Africa/Abidjan", example="Africa/Abidjan")

class SiteCreate(SiteBase):
    organization_id: str

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None

class Site(SiteBase):
    id: str
    organization_id: str

    class Config:
        from_attributes = True
