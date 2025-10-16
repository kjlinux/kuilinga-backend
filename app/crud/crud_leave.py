from sqlalchemy.orm import Session, joinedload
from typing import Dict, Any
from app.crud.base import CRUDBase
from app.models.leave import Leave
from app.models.employee import Employee
from app.schemas.leave import LeaveCreate, LeaveUpdate

class CRUDLeave(CRUDBase[Leave, LeaveCreate, LeaveUpdate]):
    def get_multi_paginated(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> Dict[str, Any]:
        query = db.query(self.model).options(
            joinedload(Leave.employee).options(
                joinedload(Employee.department)
            ),
            joinedload(Leave.approver)
        )
        total = query.count()
        items = query.order_by(Leave.start_date.desc()).offset(skip).limit(limit).all()
        return {"items": items, "total": total}

leave = CRUDLeave(Leave)