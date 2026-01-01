from sqlalchemy.orm import Session, joinedload
from typing import Dict, Any, Optional
from sqlalchemy import or_, asc, desc
from app.crud.base import CRUDBase
from app.models.leave import Leave
from app.models.employee import Employee
from app.schemas.leave import LeaveCreate, LeaveUpdate

class CRUDLeave(CRUDBase[Leave, LeaveCreate, LeaveUpdate]):
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
            joinedload(Leave.employee).options(
                joinedload(Employee.department)
            ),
            joinedload(Leave.approver)
        )

        # Search functionality (search in leave type, status, and reason)
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Leave.leave_type.ilike(search_filter),
                    Leave.status.ilike(search_filter),
                    Leave.reason.ilike(search_filter)
                )
            )

        total = query.count()

        # Sort functionality
        if sort_by:
            valid_columns = ["leave_type", "status", "start_date", "end_date", "created_at", "updated_at"]
            if sort_by in valid_columns:
                column = getattr(Leave, sort_by)
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
            else:
                query = query.order_by(Leave.start_date.desc())
        else:
            query = query.order_by(Leave.start_date.desc())

        items = query.offset(skip).limit(limit).all()
        return {"items": items, "total": total}

leave = CRUDLeave(Leave)