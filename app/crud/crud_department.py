from sqlalchemy.orm import Session, joinedload
from typing import Dict, Any
from app.crud.base import CRUDBase
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate

class CRUDDepartment(CRUDBase[Department, DepartmentCreate, DepartmentUpdate]):
    def get_multi_paginated(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> Dict[str, Any]:
        query = db.query(self.model).options(
            joinedload(Department.site),
            joinedload(Department.manager)
        )
        total = query.count()
        items = query.order_by(Department.name).offset(skip).limit(limit).all()
        return {"items": items, "total": total}

    def count_by_site(self, db: Session, *, site_id: str) -> int:
        return db.query(self.model).filter(Department.site_id == site_id).count()

department = CRUDDepartment(Department)