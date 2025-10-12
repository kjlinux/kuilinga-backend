import enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from .base import BaseModel

class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class Leave(BaseModel):
    __tablename__ = "leaves"

    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING, nullable=False)
    reason = Column(Text, nullable=True)
    leave_type = Column(String, nullable=False, default="leave") # e.g., 'leave', 'absence', 'sick'

    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    approved_by_id = Column(String, ForeignKey("users.id"), nullable=True)

    employee = relationship("Employee", back_populates="leaves")
    approved_by = relationship("User")
