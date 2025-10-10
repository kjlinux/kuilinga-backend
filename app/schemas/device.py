from pydantic import BaseModel, Field
from typing import Optional
from app.models.device import DeviceStatus

# Propriétés partagées pour les devices
class DeviceBase(BaseModel):
    serial_number: str = Field(..., example="SN-DEVICE-001")
    type: Optional[str] = Field("Pointage Fixe", example="Terminal v2")
    status: DeviceStatus = Field(DeviceStatus.OFFLINE, example="online")

# Propriétés pour la création d'un device
class DeviceCreate(DeviceBase):
    organization_id: str
    site_id: Optional[str] = None

# Propriétés pour la mise à jour d'un device
class DeviceUpdate(BaseModel):
    serial_number: Optional[str] = None
    type: Optional[str] = None
    status: Optional[DeviceStatus] = None
    site_id: Optional[str] = None

# Propriétés à retourner via l'API
class Device(DeviceBase):
    id: str
    organization_id: str
    site_id: Optional[str] = None

    class Config:
        from_attributes = True