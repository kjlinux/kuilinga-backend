from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate

class CRUDEmployee(CRUDBase[Employee, EmployeeCreate, EmployeeUpdate]):
    def get_multi_by_organization(
        self, db: Session, *, organization_id: str, skip: int = 0, limit: int = 100
    ) -> Dict[str, Any]:
        query = db.query(self.model).filter(Employee.organization_id == organization_id)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return {"items": items, "total": total}

employee = CRUDEmployee(Employee)