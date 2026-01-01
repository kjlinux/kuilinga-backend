from sqlalchemy.orm import Session, joinedload
from typing import Dict, Any, Optional
from sqlalchemy import or_, asc, desc
from app.crud.base import CRUDBase
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate

class CRUDDepartment(CRUDBase[Department, DepartmentCreate, DepartmentUpdate]):
    def get_multi_paginated(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "asc"
    ) -> Dict[str, Any]:
        query = db.query(self.model).options(
            joinedload(Department.site),
            joinedload(Department.manager)
        )

        # Search functionality
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Department.name.ilike(search_filter),
                    Department.description.ilike(search_filter)
                )
            )

        total = query.count()

        # Sort functionality
        if sort_by:
            valid_columns = ["name", "description", "created_at", "updated_at"]
            if sort_by in valid_columns:
                column = getattr(Department, sort_by)
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
            else:
                query = query.order_by(Department.name)
        else:
            query = query.order_by(Department.name)

        items = query.offset(skip).limit(limit).all()
        return {"items": items, "total": total}

    def count_by_site(self, db: Session, *, site_id: str) -> int:
        return db.query(self.model).filter(Department.site_id == site_id).count()

department = CRUDDepartment(Department)