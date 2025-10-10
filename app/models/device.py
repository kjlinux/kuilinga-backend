import enum
from sqlalchemy import Column, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class DeviceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"

class Device(BaseModel):
    __tablename__ = "devices"

    serial_number = Column(String, unique=True, index=True, nullable=False)
    type = Column(String, nullable=True)
    status = Column(Enum(DeviceStatus), default=DeviceStatus.OFFLINE, nullable=False)

    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    site_id = Column(String, ForeignKey("sites.id"), nullable=True)

    organization = relationship("Organization", back_populates="devices")
    site = relationship("Site")
    attendances = relationship("Attendance", back_populates="device")