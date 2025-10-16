from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date
from app.models.leave import LeaveStatus, LeaveType

# Schéma pour le département de l'employé en congé
class LeaveDepartment(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True

# Schéma pour l'employé en congé
class LeaveEmployee(BaseModel):
    id: str
    first_name: str
    last_name: str
    department: Optional[LeaveDepartment] = None

    full_name: Optional[str] = None

    @validator('full_name', pre=True, always=True)
    def set_full_name(cls, v, values):
        return f"{values.get('first_name', '')} {values.get('last_name', '')}".strip()

    class Config:
        from_attributes = True

# Schéma pour l'approbateur du congé
class LeaveApprover(BaseModel):
    id: str
    full_name: Optional[str] = Field(None, example="Admin User")

    class Config:
        from_attributes = True

# Schéma de base pour le congé
class LeaveBase(BaseModel):
    leave_type: LeaveType = Field(..., example=LeaveType.ANNUAL)
    start_date: date = Field(..., example="2024-12-20")
    end_date: date = Field(..., example="2024-12-30")
    reason: str = Field(..., example="Vacances annuelles")
    notes: Optional[str] = None

# Schéma pour la création d'un congé
class LeaveCreate(LeaveBase):
    employee_id: str

# Schéma pour la mise à jour (approbation/rejet)
class LeaveUpdate(BaseModel):
    status: LeaveStatus
    notes: Optional[str] = None

# Schéma complet pour retourner via l'API
class Leave(LeaveBase):
    id: str
    status: LeaveStatus
    duration: int = 0  # en jours
    employee: Optional[LeaveEmployee] = None
    approver: Optional[LeaveApprover] = None

    @validator('duration', always=True)
    def calculate_duration(cls, v, values):
        if 'start_date' in values and 'end_date' in values:
            return (values['end_date'] - values['start_date']).days + 1
        return 0

    class Config:
        from_attributes = True