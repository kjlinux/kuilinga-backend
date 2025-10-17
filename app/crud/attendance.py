from typing import Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, date
from app.crud.base import CRUDBase
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.department import Department
from app.models.site import Site
from app.models.device import Device
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate

class CRUDAttendance(CRUDBase[Attendance, AttendanceCreate, AttendanceUpdate]):
    def get_multi_paginated(
        self, db: Session, *, skip: int = 0, limit: int = 100, employee_id: str = None
    ) -> Dict[str, Any]:

        query = (
            db.query(self.model)
            .options(
                joinedload(Attendance.employee).options(
                    joinedload(Employee.department),
                    joinedload(Employee.site)
                ),
                joinedload(Attendance.device)
            )
        )

        if employee_id:
            query = query.filter(Attendance.employee_id == employee_id)

        total = query.count()

        items = (
            query.order_by(Attendance.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return {"items": items, "total": total}

    def get_multi_by_employee(
        self, db: Session, *, employee_id: str, skip: int = 0, limit: int = 100
    ) -> Dict[str, Any]:
        return self.get_multi_paginated(db, skip=skip, limit=limit, employee_id=employee_id)

    def get_last_for_employee(self, db: Session, *, employee_id: str) -> Optional[Attendance]:
        return (
            db.query(self.model)
            .filter(Attendance.employee_id == employee_id)
            .order_by(Attendance.timestamp.desc())
            .first()
        )

    def get_last_for_device(self, db: Session, *, device_id: str) -> Optional[Attendance]:
        return (
            db.query(self.model)
            .filter(Attendance.device_id == device_id)
            .order_by(Attendance.timestamp.desc())
            .first()
        )

    def count_today_for_device(self, db: Session, *, device_id: str) -> int:
        today = date.today()
        return (
            db.query(self.model)
            .filter(Attendance.device_id == device_id)
            .filter(func.date(Attendance.timestamp) == today)
            .count()
        )

attendance = CRUDAttendance(Attendance)