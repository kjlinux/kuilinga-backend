from pydantic import BaseModel, Field, validator
from typing import Optional

# Schéma pour les informations de base sur le site du département
class DepartmentSite(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True

# Schéma pour les informations de base sur le manager du département
class DepartmentManager(BaseModel):
    id: str
    first_name: str
    last_name: str

    full_name: Optional[str] = None

    @validator('full_name', pre=True, always=True)
    def set_full_name(cls, v, values):
        return f"{values.get('first_name', '')} {values.get('last_name', '')}".strip()

    class Config:
        from_attributes = True

# Schéma de base pour le département
class DepartmentBase(BaseModel):
    name: str

# Schéma pour la création d'un département
class DepartmentCreate(DepartmentBase):
    site_id: str
    manager_id: Optional[str] = None

# Schéma pour la mise à jour d'un département
class DepartmentUpdate(DepartmentBase):
    name: Optional[str] = None
    manager_id: Optional[str] = None

# Schéma complet pour retourner via l'API
class Department(DepartmentBase):
    id: str
    site: Optional[DepartmentSite] = None
    manager: Optional[DepartmentManager] = None
    employees_count: int = 0

    class Config:
        from_attributes = True