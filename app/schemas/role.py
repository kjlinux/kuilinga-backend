from pydantic import BaseModel
from typing import List

# ====================
# Permission Schemas
# ====================

class PermissionBase(BaseModel):
    name: str
    description: str | None = None

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: str

    class Config:
        orm_mode = True

# ====================
# Role Schemas
# ====================

class RoleBase(BaseModel):
    name: str
    description: str | None = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    pass

class Role(RoleBase):
    id: str
    permissions: List[Permission] = []

    class Config:
        orm_mode = True
