from pydantic import BaseModel, Field, validator
from typing import Optional, Any
from app.schemas.department import Department, DepartmentBase
from app.schemas.site import Site, SiteBase
from app.schemas.organization import Organization, OrganizationBase
from app.schemas.user import User, UserBase

# Schéma pour les informations de base sur le département de l'employé
class EmployeeDepartment(DepartmentBase):
    id: str
    name: str

    class Config:
        from_attributes = True

# Schéma pour les informations de base sur le site de l'employé
class EmployeeSite(SiteBase):
    id: str
    name: str

    class Config:
        from_attributes = True

# Schéma pour les informations de base sur l'organisation de l'employé
class EmployeeOrganization(OrganizationBase):
    id: str
    name: str

    class Config:
        from_attributes = True

# Schéma pour les informations de base sur l'utilisateur de l'employé
class EmployeeUser(UserBase):
    id: str
    is_active: bool

    class Config:
        from_attributes = True

# Propriétés partagées pour les employés
class EmployeeBase(BaseModel):
    first_name: str = Field(..., example="Jean", description="Prénom de l'employé")
    last_name: str = Field(..., example="Kouassi", description="Nom de famille de l'employé")
    email: str = Field(..., example="kouassi.jean@example.com", description="Adresse email professionnelle")
    phone: Optional[str] = Field(None, example="+2250102030405", description="Numéro de téléphone (format international)")
    employee_number: Optional[str] = Field(None, example="EMP001", description="Matricule unique de l'employé")
    position: Optional[str] = Field(None, example="Développeur Backend", description="Poste ou fonction occupée")
    badge_id: Optional[str] = Field(None, example="BADGE-KJ-001", description="Identifiant du badge RFID/NFC pour le pointage")

# Propriétés pour la création d'un employé
class EmployeeCreate(EmployeeBase):
    organization_id: str = Field(..., description="ID de l'organisation d'appartenance")
    department_id: Optional[str] = Field(None, description="ID du département (optionnel)")
    site_id: Optional[str] = Field(None, description="ID du site de travail (optionnel)")
    user_id: Optional[str] = Field(None, description="ID du compte utilisateur associé (optionnel)")

# Propriétés pour la mise à jour d'un employé
class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, description="Prénom de l'employé")
    last_name: Optional[str] = Field(None, description="Nom de famille de l'employé")
    email: Optional[str] = Field(None, description="Adresse email professionnelle")
    phone: Optional[str] = Field(None, description="Numéro de téléphone (format international)")
    employee_number: Optional[str] = Field(None, description="Matricule unique de l'employé")
    department_id: Optional[str] = Field(None, description="ID du département")
    site_id: Optional[str] = Field(None, description="ID du site de travail")
    position: Optional[str] = Field(None, description="Poste ou fonction occupée")
    badge_id: Optional[str] = Field(None, description="Identifiant du badge RFID/NFC")

# Propriétés à retourner via l'API
class Employee(EmployeeBase):
    id: str = Field(..., description="Identifiant unique de l'employé")
    status: str = Field("Inactif", description="Statut calculé automatiquement (Actif/Inactif)")
    department: Optional[EmployeeDepartment] = Field(None, description="Département de l'employé")
    site: Optional[EmployeeSite] = Field(None, description="Site de travail de l'employé")
    organization: Optional[EmployeeOrganization] = Field(None, description="Organisation d'appartenance")
    user: Optional[EmployeeUser] = Field(None, description="Compte utilisateur associé")

    @validator('status', always=True)
    def determine_status(cls, v, values):
        if values.get('user') and values['user'].is_active:
            return "Actif"
        return "Inactif"

    class Config:
        from_attributes = True