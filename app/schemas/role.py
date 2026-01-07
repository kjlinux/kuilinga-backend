from pydantic import BaseModel, Field
from typing import List

# ====================
# Permission Schemas
# ====================

class PermissionBase(BaseModel):
    name: str = Field(..., description="Nom de la permission (ex: 'employee:read', 'attendance:create')")
    description: str | None = Field(None, description="Description de la permission")

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseModel):
    name: str | None = Field(None, description="Nom de la permission")
    description: str | None = Field(None, description="Description de la permission")

class Permission(PermissionBase):
    id: str = Field(..., description="Identifiant unique de la permission")

    class Config:
        from_attributes = True

# ====================
# Role Schemas
# ====================

class RoleBase(BaseModel):
    name: str = Field(..., description="Nom du rôle (ex: 'admin', 'manager', 'employee')")
    description: str | None = Field(None, description="Description des responsabilités du rôle")

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: str | None = Field(None, description="Nom du rôle")
    description: str | None = Field(None, description="Description du rôle")

class Role(RoleBase):
    id: str = Field(..., description="Identifiant unique du rôle")
    permissions: List[Permission] = Field([], description="Liste des permissions associées au rôle")

    class Config:
        from_attributes = True
