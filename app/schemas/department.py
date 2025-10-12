from pydantic import BaseModel
from typing import Optional

class DepartmentBase(BaseModel):
    name: str

class DepartmentCreate(DepartmentBase):
    site_id: str
    manager_id: Optional[str] = None

class DepartmentUpdate(DepartmentBase):
    name: Optional[str] = None
    manager_id: Optional[str] = None

class Department(DepartmentBase):
    id: str
    site_id: str
    manager_id: Optional[str] = None

    class Config:
        orm_mode = True
