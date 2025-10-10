from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate

class CRUDEmployee(CRUDBase[Employee, EmployeeCreate, EmployeeUpdate]):
    def get_multi_by_organization(
        self, db: Session, *, organization_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Employee]:
        return (
            db.query(self.model)
            .filter(Employee.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

employee = CRUDEmployee(Employee)