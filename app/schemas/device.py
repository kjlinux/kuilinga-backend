from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.device import DeviceStatus
from .organization import OrganizationBase
from .site import SiteBase

class DeviceOrganization(OrganizationBase):
    id: str
    name: str

    class Config:
        from_attributes = True

class DeviceSite(SiteBase):
    id: str
    name: str

    class Config:
        from_attributes = True

# Propriétés partagées pour les appareils
class DeviceBase(BaseModel):
    serial_number: str = Field(..., example="SN-DEVICE-001")
    type: str = Field("Terminal Fixe", example="Terminal v2") # Renamed from model
    status: DeviceStatus = Field(DeviceStatus.OFFLINE, example="online")

# Propriétés pour la création d'un appareil
class DeviceCreate(DeviceBase):
    organization_id: str
    site_id: Optional[str] = None

# Propriétés pour la mise à jour d'un appareil
class DeviceUpdate(BaseModel):
    serial_number: Optional[str] = None
    type: Optional[str] = None
    status: Optional[DeviceStatus] = None
    site_id: Optional[str] = None

# Propriétés à retourner via l'API
class Device(DeviceBase):
    id: str
    organization: Optional[DeviceOrganization] = None
    site: Optional[DeviceSite] = None
    last_attendance_timestamp: Optional[datetime] = None
    daily_attendance_count: int = 0

    class Config:
        from_attributes = True