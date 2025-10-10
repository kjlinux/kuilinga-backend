from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from app.models.device import DeviceStatus

# Schéma de base pour Device
class DeviceBase(BaseModel):
    serial: str = Field(..., example="XYZ-123456789")
    type: Optional[str] = Field(None, example="Terminal-A")
    status: DeviceStatus = Field(DeviceStatus.OFFLINE, example=DeviceStatus.ONLINE)

class DeviceCreate(DeviceBase):
    site_id: UUID

class DeviceUpdate(BaseModel):
    serial: Optional[str] = None
    type: Optional[str] = None
    status: Optional[DeviceStatus] = None
    site_id: Optional[UUID] = None

class Device(DeviceBase):
    id: UUID
    site_id: UUID

    class Config:
        from_attributes = True