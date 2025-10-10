import enum
from sqlalchemy import Column, DateTime, String, JSON, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class AttendanceType(str, enum.Enum):
    """Énumération pour les types de pointage"""
    IN = "in"
    OUT = "out"

class Attendance(BaseModel):
    """Modèle de données pour les pointages"""
    __tablename__ = "attendances"

    timestamp = Column(DateTime(timezone=True), nullable=False)
    type = Column(Enum(AttendanceType), nullable=False)
    geo = Column(String)
    metadata = Column(JSON)

    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)

    employee = relationship("Employee", back_populates="attendances")
    device = relationship("Device", back_populates="attendances")