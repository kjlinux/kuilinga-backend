from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from app.models.leave import LeaveStatus, LeaveType
from .user import User
from .employee import Employee

class LeaveBase(BaseModel):
    leave_type: LeaveType = Field(..., example=LeaveType.ANNUAL)
    start_date: date = Field(..., example="2024-12-20")
    end_date: date = Field(..., example="2024-12-30")
    reason: str = Field(..., example="Vacances annuelles")

class LeaveCreate(LeaveBase):
    employee_id: str

class LeaveUpdate(BaseModel):
    status: Optional[LeaveStatus] = None
    notes: Optional[str] = None

class Leave(LeaveBase):
    id: str
    employee_id: str
    status: LeaveStatus
    approver_id: Optional[str] = None
    notes: Optional[str] = None
    employee: Optional[Employee] = None
    approver: Optional[User] = None


    class Config:
        from_attributes = True
