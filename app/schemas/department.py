from pydantic import BaseModel, Field, validator
from typing import Optional

# Schéma pour les informations de base sur le site du département
class DepartmentSite(BaseModel):
    id: str = Field(..., description="Identifiant unique du site")
    name: str = Field(..., description="Nom du site")

    class Config:
        from_attributes = True

# Schéma pour les informations de base sur le manager du département
class DepartmentManager(BaseModel):
    id: str = Field(..., description="Identifiant unique du manager")
    first_name: str = Field(..., description="Prénom du manager")
    last_name: str = Field(..., description="Nom de famille du manager")

    full_name: Optional[str] = Field(None, description="Nom complet calculé automatiquement")

    @validator('full_name', pre=True, always=True)
    def set_full_name(cls, v, values):
        return f"{values.get('first_name', '')} {values.get('last_name', '')}".strip()

    class Config:
        from_attributes = True

# Schéma de base pour le département
class DepartmentBase(BaseModel):
    name: str = Field(..., description="Nom du département")

# Schéma pour la création d'un département
class DepartmentCreate(DepartmentBase):
    site_id: str = Field(..., description="ID du site auquel appartient le département")
    manager_id: Optional[str] = Field(None, description="ID de l'employé responsable du département")

# Schéma pour la mise à jour d'un département
class DepartmentUpdate(DepartmentBase):
    name: Optional[str] = Field(None, description="Nom du département")
    manager_id: Optional[str] = Field(None, description="ID de l'employé responsable du département")

# Schéma complet pour retourner via l'API
class Department(DepartmentBase):
    id: str = Field(..., description="Identifiant unique du département")
    site: Optional[DepartmentSite] = Field(None, description="Site d'appartenance")
    manager: Optional[DepartmentManager] = Field(None, description="Manager responsable du département")
    employees_count: int = Field(0, description="Nombre d'employés dans le département")

    class Config:
        from_attributes = True