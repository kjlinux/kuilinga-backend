from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Organization, User, Site, Device
from app.models.device import DeviceStatus

# I will add dashboard-specific CRUD functions here.
class CRUDDashboard:
    def get_active_organizations_count(self, db: Session) -> int:
        return db.query(Organization).filter(Organization.is_active == True).count()

    def get_users_per_organization(self, db: Session) -> list[dict]:
        return (
            db.query(Organization.name, func.count(User.id).label("user_count"))
            .join(User, Organization.id == User.organization_id)
            .group_by(Organization.name)
            .all()
        )

    def get_sites_per_organization(self, db: Session) -> list[dict]:
        return (
            db.query(Organization.name, func.count(Site.id).label("site_count"))
            .join(Site, Organization.id == Site.organization_id)
            .group_by(Organization.name)
            .all()
        )

    def get_device_status_ratio(self, db: Session) -> list[dict]:
        return (
            db.query(Device.status, func.count(Device.id).label("count"))
            .group_by(Device.status)
            .all()
        )

    def get_daily_attendance_count(self, db: Session) -> int:
        from app.models import Attendance
        # Assuming timestamp is stored in UTC and we compare against UTC now
        return db.query(func.count(Attendance.id)).filter(func.date(Attendance.timestamp) == func.current_date()).scalar()

    def get_daily_presence_and_total_employees(self, db: Session, organization_id: str) -> tuple[int, int]:
        from app.models import Employee, Attendance
        total_employees = db.query(func.count(Employee.id)).filter(Employee.organization_id == organization_id).scalar()
        present_employees = (
            db.query(func.count(func.distinct(Attendance.employee_id)))
            .join(Employee)
            .filter(Employee.organization_id == organization_id)
            .filter(func.date(Attendance.timestamp) == func.current_date())
            .scalar()
        )
        return present_employees, total_employees

    def get_daily_tardiness_count(self, db: Session, organization_id: str) -> int:
        # This function is a placeholder. A full implementation requires a 'Shift' model
        # with expected start times for each employee. The current 'shift.py' model is empty,
        # so this logic cannot be implemented.
        return 0

    def get_plan_distribution(self, db: Session) -> list[dict]:
        return (
            db.query(Organization.plan, func.count(Organization.id).label("count"))
            .group_by(Organization.plan)
            .all()
        )

    def get_presence_evolution_last_30_days(self, db: Session, organization_id: str) -> list[dict]:
        from datetime import date, timedelta
        from app.models import Attendance, Employee

        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        return (
            db.query(
                func.date(Attendance.timestamp).label("date"),
                func.count(func.distinct(Attendance.employee_id)).label("presence_count"),
            )
            .join(Employee)
            .filter(Employee.organization_id == organization_id)
            .filter(func.date(Attendance.timestamp) >= thirty_days_ago)
            .group_by(func.date(Attendance.timestamp))
            .order_by(func.date(Attendance.timestamp))
            .all()
        )

    def get_top_10_organizations_by_employees(self, db: Session) -> list[dict]:
        from app.models import Organization, Employee
        return (
            db.query(Organization.name, func.count(Employee.id).label("employee_count"))
            .join(Employee, Organization.id == Employee.organization_id)
            .group_by(Organization.name)
            .order_by(func.count(Employee.id).desc())
            .limit(10)
            .all()
        )

    def get_presence_absence_tardiness_distribution(self, db: Session, organization_id: str) -> dict:
        present, total = self.get_daily_presence_and_total_employees(db, organization_id)
        absent = total - present
        tardy = self.get_daily_tardiness_count(db, organization_id) # This will be 0 for now
        return {"present": present, "absent": absent, "tardy": tardy}

    def get_real_time_attendances(self, db: Session, organization_id: str) -> list:
        from datetime import datetime, timedelta
        from app.models import Attendance, Employee
        two_hours_ago = datetime.utcnow() - timedelta(hours=2)
        return (
            db.query(Attendance)
            .join(Employee)
            .filter(Employee.organization_id == organization_id)
            .filter(Attendance.timestamp >= two_hours_ago)
            .order_by(Attendance.timestamp.desc())
            .all()
        )

    def get_attendance_rate(self, db: Session, organization_id: str) -> float:
        present_employees, total_employees = self.get_daily_presence_and_total_employees(db, organization_id)
        if total_employees == 0:
            return 0.0
        return (present_employees / total_employees) * 100

    def get_total_work_hours(self, db: Session, organization_id: str) -> float:
        # This function is a placeholder. A robust implementation would require pairing 'IN' and 'OUT'
        # events for each employee for each day, handling cases of missing check-outs, and summing the
        # durations. This is a complex operation that is best handled by a dedicated time and attendance
        # calculation engine, possibly in an offline process.
        return 0.0

    def get_pending_leaves_count(self, db: Session, organization_id: str) -> int:
        from app.models import Leave, Employee
        return (
            db.query(func.count(Leave.id))
            .join(Employee)
            .filter(Employee.organization_id == organization_id, Leave.status == "PENDING")
            .scalar()
        )

    def get_employee_today_attendances(self, db: Session, employee_id: str) -> list:
        from app.models import Attendance
        return (
            db.query(Attendance)
            .filter(Attendance.employee_id == employee_id)
            .filter(func.date(Attendance.timestamp) == func.current_date())
            .all()
        )

    def get_employee_monthly_attendance_rate(self, db: Session, employee_id: str) -> float:
        # Simplified: assumes 22 working days in a month.
        from app.models import Attendance
        from sqlalchemy import text
        from datetime import datetime

        start_of_month = datetime.today().replace(day=1)

        days_present = (
            db.query(func.count(func.distinct(func.date(Attendance.timestamp))))
            .filter(Attendance.employee_id == employee_id)
            .filter(Attendance.timestamp >= start_of_month)
            .scalar()
        )
        return (days_present / 22) * 100

    def get_employee_leave_balance(self, db: Session, employee_id: str) -> dict:
        from app.models import Leave
        # This is a simplified implementation. A real system would have a more complex
        # model for leave entitlement and balance.
        total_entitlement = 25  # Assuming a fixed entitlement for all employees.
        used_leaves = (
            db.query(func.count(Leave.id))
            .filter(Leave.employee_id == employee_id, Leave.status == "APPROVED")
            .scalar()
        )
        return {"total": total_entitlement, "used": used_leaves, "available": total_entitlement - used_leaves}

    def get_attendance_per_device(self, db: Session, organization_id: str) -> list[dict]:
        from app.models import Device, Attendance
        return (
            db.query(Device.serial_number, func.count(Attendance.id).label("attendance_count"))
            .join(Attendance, Device.id == Attendance.device_id)
            .filter(Device.organization_id == organization_id)
            .group_by(Device.serial_number)
            .all()
        )

    def get_tardiness_by_day_of_week(self, db: Session, organization_id: str) -> list[dict]:
        # This function is a placeholder. A full implementation would require a 'Shifts' table
        # to define expected start times, logic to identify late arrivals, and then group them
        # by the day of the week. This is a complex query that is beyond the scope of this
        # initial implementation.
        return [
            {"day": "Monday", "tardy_count": 0},
            {"day": "Tuesday", "tardy_count": 0},
            {"day": "Wednesday", "tardy_count": 0},
            {"day": "Thursday", "tardy_count": 0},
            {"day": "Friday", "tardy_count": 0},
        ]


dashboard = CRUDDashboard()