from typing import Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
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
        organization_id: Optional[str] = None
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

        total = query.count()

        items = (
            query.order_by(Employee.last_name, Employee.first_name)
            .offset(skip)
            .limit(limit)
            .all()
        )

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