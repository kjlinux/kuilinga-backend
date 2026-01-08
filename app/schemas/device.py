from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.device import DeviceStatus, DeliveryMethod
from .organization import OrganizationBase
from .site import SiteBase

class DeviceOrganization(OrganizationBase):
    id: str = Field(..., description="Identifiant unique de l'organisation")
    name: str = Field(..., description="Nom de l'organisation")

    class Config:
        from_attributes = True

class DeviceSite(SiteBase):
    id: str = Field(..., description="Identifiant unique du site")
    name: str = Field(..., description="Nom du site")

    class Config:
        from_attributes = True

# Propriétés partagées pour les appareils
class DeviceBase(BaseModel):
    serial_number: str = Field(..., example="SN-DEVICE-001", description="Numéro de série unique du terminal")
    type: str = Field("Terminal Fixe", example="Terminal v2", description="Type de terminal (ex: 'Terminal Fixe', 'Terminal Mobile')")
    status: DeviceStatus = Field(DeviceStatus.OFFLINE, example="online", description="État du terminal : 'online', 'offline', 'maintenance'")
    delivery_method: DeliveryMethod = Field(
        DeliveryMethod.mqtt,
        example="mqtt",
        description="Méthode de communication avec le terminal : 'http' pour requêtes HTTP directes, 'mqtt' pour communication via broker MQTT"
    )

# Propriétés pour la création d'un appareil
class DeviceCreate(DeviceBase):
    organization_id: str = Field(..., description="ID de l'organisation propriétaire")
    site_id: Optional[str] = Field(None, description="ID du site où est installé le terminal")

# Propriétés pour la mise à jour d'un appareil
class DeviceUpdate(BaseModel):
    serial_number: Optional[str] = Field(None, description="Numéro de série du terminal")
    type: Optional[str] = Field(None, description="Type de terminal")
    status: Optional[DeviceStatus] = Field(None, description="État du terminal")
    site_id: Optional[str] = Field(None, description="ID du site")
    delivery_method: Optional[DeliveryMethod] = Field(None, description="Méthode de communication (http ou mqtt)")


# Schema interne pour la mise à jour du heartbeat (non exposé à l'API)
class DeviceHeartbeatUpdate(BaseModel):
    """Schema pour la mise à jour automatique via heartbeat MQTT."""
    status: DeviceStatus = DeviceStatus.ONLINE
    last_seen_at: datetime
    firmware_version: Optional[str] = None
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    wifi_rssi: Optional[int] = Field(None, le=0)  # RSSI est toujours négatif

# Propriétés à retourner via l'API
class Device(DeviceBase):
    id: str = Field(..., description="Identifiant unique du terminal")
    organization: Optional[DeviceOrganization] = Field(None, description="Organisation propriétaire")
    site: Optional[DeviceSite] = Field(None, description="Site d'installation")
    last_attendance_timestamp: Optional[datetime] = Field(None, description="Date/heure du dernier pointage enregistré")
    daily_attendance_count: int = Field(0, description="Nombre de pointages du jour")

    # Heartbeat / monitoring fields
    last_seen_at: Optional[datetime] = Field(None, description="Dernière communication reçue du terminal")
    firmware_version: Optional[str] = Field(None, description="Version du firmware")
    battery_level: Optional[int] = Field(None, description="Niveau de batterie (0-100%)")
    wifi_rssi: Optional[int] = Field(None, description="Force du signal WiFi en dBm")

    class Config:
        from_attributes = True