from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.attendance import Attendance
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate

class CRUDAttendance(CRUDBase[Attendance, AttendanceCreate, AttendanceUpdate]):
    def get_multi_by_employee(
        self, db: Session, *, employee_id: str, skip: int = 0, limit: int = 100
    ) -> Dict[str, Any]:
        query = db.query(self.model).filter(Attendance.employee_id == employee_id)
        total = query.count()
        items = (
            query.order_by(Attendance.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return {"items": items, "total": total}

attendance = CRUDAttendance(Attendance)