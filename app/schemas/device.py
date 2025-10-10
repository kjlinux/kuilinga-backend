from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.device import DeviceType, DeviceStatus


class DeviceBase(BaseModel):
    """Schéma de base device"""
    serial_number: str
    name: str
    device_type: DeviceType
    firmware_version: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = {}
    metadata: Optional[Dict[str, Any]] = {}


class DeviceCreate(DeviceBase):
    """Schéma de création de device"""
    organization_id: int


class DeviceUpdate(BaseModel):
    """Schéma de mise à jour de device"""
    name: Optional[str] = None
    status: Optional[DeviceStatus] = None
    is_online: Optional[bool] = None
    firmware_version: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class Device(DeviceBase):
    """Schéma de réponse device"""
    id: int
    organization_id: int
    status: DeviceStatus
    is_online: bool
    last_ping: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DeviceList(BaseModel):
    """Liste paginée de devices"""
    total: int
    page: int
    page_size: int
    devices: list[Device]


class DevicePing(BaseModel):
    """Schéma de ping device"""
    device_id: UUID
    timestamp: datetime
    status: str
    metadata: Optional[Dict[str, Any]] = {}


class DeviceStats(BaseModel):
    """Statistiques d'un device"""
    device_id: UUID
    device_name: str
    total_attendances: int
    attendances_today: int
    last_attendance: Optional[datetime] = None
    uptime_percentage: float