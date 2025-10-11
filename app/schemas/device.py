from pydantic import BaseModel, Field
from typing import Optional
from app.models.device import DeviceStatus

# Propriétés partagées pour les appareils
class DeviceBase(BaseModel):
    serial_number: str = Field(..., example="SN-DEVICE-001")
    model: str = Field("Pointage Fixe", example="Terminal v2")
    status: DeviceStatus = Field(DeviceStatus.OFFLINE, example="online")
    organization_id: str

# Propriétés pour la création d'un appareil
class DeviceCreate(DeviceBase):
    pass

# Propriétés pour la mise à jour d'un appareil
class DeviceUpdate(BaseModel):
    serial_number: Optional[str] = None
    model: Optional[str] = None
    status: Optional[DeviceStatus] = None

# Propriétés à retourner via l'API
class Device(DeviceBase):
    id: str

    class Config:
        from_attributes = True
