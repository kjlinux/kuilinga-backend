from typing import Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, asc, desc
from app.crud.base import CRUDBase
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate

class CRUDEmployee(CRUDBase[Employee, EmployeeCreate, EmployeeUpdate]):
    def get_multi_paginated(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        organization_id: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "asc"
    ) -> Dict[str, Any]:

        query = (
            db.query(self.model)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.site),
                joinedload(Employee.organization),
                joinedload(Employee.user)
            )
        )

        if organization_id:
            query = query.filter(Employee.organization_id == organization_id)

        # Search functionality
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Employee.first_name.ilike(search_filter),
                    Employee.last_name.ilike(search_filter),
                    Employee.email.ilike(search_filter),
                    Employee.badge_id.ilike(search_filter),
                    Employee.phone.ilike(search_filter),
                    Employee.position.ilike(search_filter)
                )
            )

        total = query.count()

        # Sort functionality
        if sort_by:
            # Validate and get the column
            valid_columns = ["first_name", "last_name", "email", "badge_id", "position", "created_at", "updated_at"]
            if sort_by in valid_columns:
                column = getattr(Employee, sort_by)
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
            else:
                # Default ordering if invalid sort_by
                query = query.order_by(Employee.last_name, Employee.first_name)
        else:
            # Default ordering
            query = query.order_by(Employee.last_name, Employee.first_name)

        items = query.offset(skip).limit(limit).all()

        return {"items": items, "total": total}

    def get_multi_by_organization(
        self, db: Session, *, organization_id: str, skip: int = 0, limit: int = 100
    ) -> Dict[str, Any]:
        # This method can now use the more advanced one
        return self.get_multi_paginated(db, skip=skip, limit=limit, organization_id=organization_id)

    def count_by_organization(self, db: Session, *, organization_id: str) -> int:
        return db.query(self.model).filter(Employee.organization_id == organization_id).count()

    def count_by_site(self, db: Session, *, site_id: str) -> int:
        return db.query(self.model).filter(Employee.site_id == site_id).count()

    def count_by_department(self, db: Session, *, department_id: str) -> int:
        return db.query(self.model).filter(Employee.department_id == department_id).count()

employee = CRUDEmployee(Employee)