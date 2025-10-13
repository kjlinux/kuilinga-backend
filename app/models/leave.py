import enum
from sqlalchemy import Column, String, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from .base import BaseModel

class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class LeaveType(str, enum.Enum):
    ANNUAL = "annual"
    SICK = "sick"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    UNPAID = "unpaid"
    OTHER = "other"


class Leave(BaseModel):
    __tablename__ = "leaves"

    employee_id = Column(String, ForeignKey("employees.id"), nullable=False)
    approver_id = Column(String, ForeignKey("users.id"), nullable=True)

    leave_type = Column(Enum(LeaveType), nullable=False, default=LeaveType.OTHER)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(Enum(LeaveStatus), nullable=False, default=LeaveStatus.PENDING)
    notes = Column(String, nullable=True)

    employee = relationship("Employee", back_populates="leaves")
    approver = relationship("User", back_populates="approved_leaves")
