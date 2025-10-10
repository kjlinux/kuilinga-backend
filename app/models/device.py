import enum
from sqlalchemy import Column, String, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class DeviceStatus(str, enum.Enum):
    """Énumération pour les statuts de device"""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"

class Device(BaseModel):
    """Modèle de données pour les devices"""
    __tablename__ = "devices"

    serial = Column(String, unique=True, index=True, nullable=False)
    type = Column(String)
    status = Column(Enum(DeviceStatus), nullable=False, default=DeviceStatus.OFFLINE)
    site_id = Column(ForeignKey("sites.id"), nullable=False)

    site = relationship("Site")
    attendances = relationship("Attendance", back_populates="device")