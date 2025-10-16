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
    first_name: str = Field(..., example="Jean")
    last_name: str = Field(..., example="Kouassi")
    email: str = Field(..., example="kouassi.jean@example.com")
    phone: Optional[str] = Field(None, example="+2250102030405")
    employee_number: Optional[str] = Field(None, example="EMP001")
    position: Optional[str] = Field(None, example="Développeur Backend")
    badge_id: Optional[str] = Field(None, example="BADGE-KJ-001")

# Propriétés pour la création d'un employé
class EmployeeCreate(EmployeeBase):
    organization_id: str
    department_id: Optional[str] = None
    site_id: Optional[str] = None
    user_id: Optional[str] = None

# Propriétés pour la mise à jour d'un employé
class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    employee_number: Optional[str] = None
    department_id: Optional[str] = None
    site_id: Optional[str] = None
    position: Optional[str] = None
    badge_id: Optional[str] = None

# Propriétés à retourner via l'API
class Employee(EmployeeBase):
    id: str
    status: str = "Inactif" # Valeur par défaut
    department: Optional[EmployeeDepartment] = None
    site: Optional[EmployeeSite] = None
    organization: Optional[EmployeeOrganization] = None
    user: Optional[EmployeeUser] = None # Pour dériver le statut

    @validator('status', always=True)
    def determine_status(cls, v, values):
        if values.get('user') and values['user'].is_active:
            return "Actif"
        return "Inactif"

    class Config:
        from_attributes = True