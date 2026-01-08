import enum
from sqlalchemy import Column, String, Enum, ForeignKey, DateTime, Integer, Float
from sqlalchemy.orm import relationship
from .base import BaseModel


class DeviceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class DeliveryMethod(str, enum.Enum):
    """Méthode de communication avec le terminal IoT."""
    http = "http"
    mqtt = "mqtt"


class Device(BaseModel):
    __tablename__ = "devices"

    serial_number = Column(String, unique=True, index=True, nullable=False)
    type = Column(String, nullable=True)
    status = Column(Enum(DeviceStatus), default=DeviceStatus.OFFLINE, nullable=False)
    delivery_method = Column(
        Enum(DeliveryMethod),
        default=DeliveryMethod.mqtt,
        nullable=False,
        comment="Méthode de communication: http ou mqtt"
    )

    # Heartbeat tracking fields
    last_seen_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Dernière communication reçue du terminal (heartbeat ou pointage)"
    )
    firmware_version = Column(
        String(50),
        nullable=True,
        comment="Version du firmware du terminal"
    )
    battery_level = Column(
        Integer,
        nullable=True,
        comment="Niveau de batterie en pourcentage (0-100)"
    )
    wifi_rssi = Column(
        Integer,
        nullable=True,
        comment="Force du signal WiFi en dBm (ex: -45)"
    )

    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    site_id = Column(String, ForeignKey("sites.id"), nullable=True)

    organization = relationship("Organization", back_populates="devices")
    site = relationship("Site")
    attendances = relationship("Attendance", back_populates="device")