from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date
from app.models.leave import LeaveStatus, LeaveType

# Schéma pour le département de l'employé en congé
class LeaveDepartment(BaseModel):
    id: str = Field(..., description="Identifiant unique du département")
    name: str = Field(..., description="Nom du département")

    class Config:
        from_attributes = True

# Schéma pour l'employé en congé
class LeaveEmployee(BaseModel):
    id: str = Field(..., description="Identifiant unique de l'employé")
    first_name: str = Field(..., description="Prénom de l'employé")
    last_name: str = Field(..., description="Nom de famille de l'employé")
    department: Optional[LeaveDepartment] = Field(None, description="Département de l'employé")

    full_name: Optional[str] = Field(None, description="Nom complet calculé automatiquement")

    @validator('full_name', pre=True, always=True)
    def set_full_name(cls, v, values):
        return f"{values.get('first_name', '')} {values.get('last_name', '')}".strip()

    class Config:
        from_attributes = True

# Schéma pour l'approbateur du congé
class LeaveApprover(BaseModel):
    id: str = Field(..., description="Identifiant unique de l'approbateur")
    full_name: Optional[str] = Field(None, example="Admin User", description="Nom complet de l'approbateur")

    class Config:
        from_attributes = True

# Schéma de base pour le congé
class LeaveBase(BaseModel):
    leave_type: LeaveType = Field(..., example=LeaveType.ANNUAL, description="Type de congé (annuel, maladie, maternité, etc.)")
    start_date: date = Field(..., example="2024-12-20", description="Date de début du congé")
    end_date: date = Field(..., example="2024-12-30", description="Date de fin du congé")
    reason: str = Field(..., example="Vacances annuelles", description="Motif du congé")
    notes: Optional[str] = Field(None, description="Notes additionnelles")

# Schéma pour la création d'un congé
class LeaveCreate(LeaveBase):
    employee_id: str = Field(..., description="ID de l'employé concerné")

# Schéma pour la mise à jour (approbation/rejet)
class LeaveUpdate(BaseModel):
    status: LeaveStatus = Field(..., description="Nouveau statut (pending, approved, rejected)")
    notes: Optional[str] = Field(None, description="Notes de l'approbateur")

# Schéma complet pour retourner via l'API
class Leave(LeaveBase):
    id: str = Field(..., description="Identifiant unique du congé")
    status: LeaveStatus = Field(..., description="Statut de la demande (pending, approved, rejected)")
    duration: int = Field(0, description="Durée calculée en jours (incluant premier et dernier jour)")
    employee: Optional[LeaveEmployee] = Field(None, description="Employé concerné")
    approver: Optional[LeaveApprover] = Field(None, description="Utilisateur ayant approuvé/rejeté le congé")

    @validator('duration', always=True)
    def calculate_duration(cls, v, values):
        if 'start_date' in values and 'end_date' in values:
            return (values['end_date'] - values['start_date']).days + 1
        return 0

    class Config:
        from_attributes = True