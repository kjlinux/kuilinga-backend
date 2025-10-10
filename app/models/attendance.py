import enum
from sqlalchemy import Column, DateTime, String, JSON, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class AttendanceType(str, enum.Enum):
    IN = "in"
    OUT = "out"

class Attendance(BaseModel):
    __tablename__ = "attendances"

    timestamp = Column(DateTime(timezone=True), nullable=False)
    type = Column(Enum(AttendanceType), nullable=False)
    geo = Column(String, nullable=True)
    metadata = Column(JSON, nullable=True)

    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    device_id = Column(String, ForeignKey("devices.id"), nullable=True)

    employee = relationship("Employee", back_populates="attendances")
    device = relationship("Device", back_populates="attendances")