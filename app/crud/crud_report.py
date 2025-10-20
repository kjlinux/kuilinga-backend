from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from app import models
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
import calendar

class CRUDReport:
    def _get_bulk_employee_presence_details(
        self,
        db: Session,
        employee_ids: List[str],
        start_date: date,
        end_date: date,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        An efficient core method to get daily presence details for a list of employees.
        This is the heart of the N+1 query fix.
        """
        if not employee_ids:
            return {}

        # 1. Fetch all data in bulk
        attendances = db.query(models.Attendance).filter(
            models.Attendance.employee_id.in_(employee_ids),
            func.date(models.Attendance.timestamp) >= start_date,
            func.date(models.Attendance.timestamp) <= end_date,
        ).order_by(models.Attendance.timestamp).all()

        leaves = db.query(models.Leave).filter(
            models.Leave.employee_id.in_(employee_ids),
            models.Leave.status == models.LeaveStatus.APPROVED,
            models.Leave.start_date <= end_date,
            models.Leave.end_date >= start_date,
        ).all()

        # 2. Process data into efficient lookup maps
        leave_map = {emp_id: set() for emp_id in employee_ids}
        for leave in leaves:
            current_date = leave.start_date
            while current_date <= leave.end_date:
                if leave.employee_id in leave_map:
                    leave_map[leave.employee_id].add(current_date)
                current_date += timedelta(days=1)

        attendance_map = {emp_id: {} for emp_id in employee_ids}
        for att in attendances:
            day = att.timestamp.date()
            emp_id = att.employee_id
            if day not in attendance_map[emp_id]:
                attendance_map[emp_id][day] = {"check_in": None, "check_out": None}

            if att.type == models.AttendanceType.IN and attendance_map[emp_id][day]["check_in"] is None:
                attendance_map[emp_id][day]["check_in"] = att.timestamp
            elif att.type == models.AttendanceType.OUT:
                attendance_map[emp_id][day]["check_out"] = att.timestamp

        # 3. Build the final detailed structure
        results = {emp_id: [] for emp_id in employee_ids}
        for emp_id in employee_ids:
            current_date = start_date
            while current_date <= end_date:
                row = {"date": current_date, "check_in": None, "check_out": None, "total_hours": 0.0, "status": "Absent"}

                if current_date in leave_map[emp_id]:
                    row["status"] = "On Leave"
                elif current_date in attendance_map[emp_id]:
                    check_in_ts = attendance_map[emp_id][current_date].get("check_in")
                    check_out_ts = attendance_map[emp_id][current_date].get("check_out")

                    if check_in_ts:
                        row["status"] = "Present"
                        row["check_in"] = check_in_ts.strftime("%H:%M:%S")

                    if check_out_ts:
                        row["check_out"] = check_out_ts.strftime("%H:%M:%S")

                    if check_in_ts and check_out_ts:
                        row["total_hours"] = round(((check_out_ts - check_in_ts).total_seconds() / 3600), 2)

                results[emp_id].append(row)
                current_date += timedelta(days=1)

        return results

    def get_employee_presence_data(self, db: Session, *, employee_id: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Wraps the bulk fetcher for a single employee."""
        result = self._get_bulk_employee_presence_details(db, [employee_id], start_date, end_date)
        return result.get(employee_id, [])

    def get_organization_presence_data(
        self, db: Session, *, organization_id: str, start_date: date, end_date: date,
        site_ids: Optional[List[str]] = None, department_ids: Optional[List[str]] = None, employee_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Efficiently gets aggregated presence data for multiple employees in an organization."""
        query = db.query(models.Employee).options(joinedload(models.Employee.user), joinedload(models.Employee.department)).filter(models.Employee.organization_id == organization_id)

        if site_ids: query = query.filter(models.Employee.site_id.in_(site_ids))
        if department_ids: query = query.filter(models.Employee.department_id.in_(department_ids))
        if employee_ids: query = query.filter(models.Employee.id.in_(employee_ids))

        employees = query.all()
        emp_details = self._get_bulk_employee_presence_details(db, [emp.id for emp in employees], start_date, end_date)

        report_data = []
        for emp in employees:
            daily_data = emp_details.get(emp.id, [])
            report_data.append({
                "employee_id": emp.id,
                "employee_name": emp.user.full_name if emp.user else "N/A",
                "department_name": emp.department.name if emp.department else "N/A",
                "present_days": sum(1 for d in daily_data if d["status"] == "Present"),
                "absent_days": sum(1 for d in daily_data if d["status"] == "Absent"),
                "on_leave_days": sum(1 for d in daily_data if d["status"] == "On Leave"),
                "total_hours_worked": sum(d.get("total_hours", 0) for d in daily_data),
            })
        return report_data

    def get_organization_worked_hours_data(self, db: Session, *, organization_id: str, start_date: date, end_date: date, department_ids: Optional[List[str]] = None, employee_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Efficiently gets detailed daily data for multiple employees."""
        query = db.query(models.Employee).options(joinedload(models.Employee.user), joinedload(models.Employee.department)).filter(models.Employee.organization_id == organization_id)

        if department_ids: query = query.filter(models.Employee.department_id.in_(department_ids))
        if employee_ids: query = query.filter(models.Employee.id.in_(employee_ids))

        employees = query.all()
        emp_details = self._get_bulk_employee_presence_details(db, [emp.id for emp in employees], start_date, end_date)

        flat_report_data = []
        for emp in employees:
            daily_data = emp_details.get(emp.id, [])
            for day in daily_data:
                flat_report_data.append({
                    "employee_name": emp.user.full_name,
                    "department_name": emp.department.name if emp.department else 'N/A',
                    **day
                })
        return flat_report_data

    # All multi-employee functions below will now use the efficient `get_organization_presence_data`
    def get_department_presence_data(self, db: Session, *, department_id: str, start_date: date, end_date: date, employee_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        department = db.query(models.Department).filter(models.Department.id == department_id).first()
        if not department: return []
        return self.get_organization_presence_data(db, organization_id=department.organization_id, start_date=start_date, end_date=end_date, department_ids=[department_id], employee_ids=employee_ids)

    def get_team_performance_data(self, db: Session, *, department_id: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        presence_data = self.get_department_presence_data(db, department_id=department_id, start_date=start_date, end_date=end_date)
        performance_report = []
        for emp_data in presence_data:
            total_days = emp_data["present_days"] + emp_data["absent_days"]
            attendance_rate = round((emp_data["present_days"] / total_days) * 100, 2) if total_days > 0 else 0
            performance_report.append({
                "employee_id": emp_data["employee_id"],
                "employee_name": emp_data["employee_name"],
                "attendance_rate": attendance_rate,
                "total_hours_worked": emp_data["total_hours_worked"],
            })
        return performance_report

    def get_site_activity_data(self, db: Session, *, organization_id: str, start_date: date, end_date: date, site_ids: List[str]) -> List[Dict[str, Any]]:
        sites = db.query(models.Site).filter(models.Site.id.in_(site_ids), models.Site.organization_id == organization_id).all()
        site_activity_report = []
        for site in sites:
            presence_data = self.get_organization_presence_data(db, organization_id=organization_id, start_date=start_date, end_date=end_date, site_ids=[site.id])
            total_employees = len(presence_data)
            present_employees = sum(1 for row in presence_data if row['present_days'] > 0)
            on_leave_employees = sum(1 for row in presence_data if row['on_leave_days'] > 0)
            total_hours_worked = sum(row['total_hours_worked'] for row in presence_data)
            site_activity_report.append({
                "site_name": site.name,
                "total_employees": total_employees,
                "present_employees": present_employees,
                "on_leave_employees": on_leave_employees,
                "total_hours_worked": total_hours_worked,
                "average_hours_per_employee": (total_hours_worked / total_employees) if total_employees > 0 else 0,
            })
        return site_activity_report

    def get_multi_org_consolidated_data(self, db: Session, *, start_date: date, end_date: date, organization_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        org_query = db.query(models.Organization)
        if organization_ids: org_query = org_query.filter(models.Organization.id.in_(organization_ids))
        organizations = org_query.all()
        multi_org_report = []
        for org in organizations:
            presence_data = self.get_organization_presence_data(db, organization_id=org.id, start_date=start_date, end_date=end_date)
            multi_org_report.append({
                "organization_name": org.name,
                "present_days": sum(row['present_days'] for row in presence_data),
                "on_leave_days": sum(row['on_leave_days'] for row in presence_data),
                "total_hours_worked": sum(row['total_hours_worked'] for row in presence_data),
            })
        return multi_org_report

    # These two functions remain largely the same as they were already specific
    def get_employee_monthly_summary_data(self, db: Session, *, employee_id: str, year: int, month: int) -> Dict[str, Any]:
        _, num_days = calendar.monthrange(year, month)
        start_date, end_date = date(year, month, 1), date(year, month, num_days)
        daily_data = self.get_employee_presence_data(db, employee_id=employee_id, start_date=start_date, end_date=end_date)
        if not daily_data: return {}
        present_days = sum(1 for r in daily_data if r["status"] == "Present")
        workdays = sum(1 for d in daily_data if d['date'].weekday() < 5 and d['status'] != 'On Leave')
        total_hours_worked = sum(r.get("total_hours", 0) for r in daily_data)
        theoretical_hours = workdays * 8 # NOTE: Placeholder logic
        return {
            "summary": {
                "present_days": present_days,
                "absent_days": sum(1 for r in daily_data if r["status"] == "Absent"),
                "on_leave_days": sum(1 for r in daily_data if r["status"] == "On Leave"),
                "total_hours_worked": round(total_hours_worked, 2),
                "theoretical_hours": theoretical_hours,
                "overtime_hours": round(max(0, total_hours_worked - theoretical_hours), 2),
                "attendance_rate": round((present_days / workdays) * 100, 2) if workdays > 0 else 0,
            },
            "daily_data": [{"date": r["date"].strftime("%d"), "hours": r["total_hours"]} for r in daily_data],
            "period": start_date.strftime("%B %Y")
        }

    def get_organization_leaves_data(self, db: Session, *, organization_id: str, start_date: date, end_date: date, leave_type: Optional[models.LeaveType] = None, status: Optional[models.LeaveStatus] = None, department_ids: Optional[List[str]] = None, employee_ids: Optional[List[str]] = None) -> List[models.Leave]:
        query = db.query(models.Leave).join(models.Employee).filter(
            models.Employee.organization_id == organization_id,
            models.Leave.start_date <= end_date,
            models.Leave.end_date >= start_date,
        ).options(joinedload(models.Leave.employee).joinedload(models.Employee.user), joinedload(models.Leave.employee).joinedload(models.Employee.department))
        if department_ids: query = query.filter(models.Employee.department_id.in_(department_ids))
        if employee_ids: query = query.filter(models.Leave.employee_id.in_(employee_ids))
        if leave_type: query = query.filter(models.Leave.leave_type == leave_type)
        if status: query = query.filter(models.Leave.status == status)
        return query.order_by(models.Leave.start_date).all()

    def get_employee_leaves_data(
        self,
        db: Session,
        *,
        employee_id: str,
        year: int,
        leave_type: Optional[models.LeaveType] = None,
        status: Optional[models.LeaveStatus] = None,
    ) -> List[models.Leave]:
        """
        Fetches leave records for a single employee for a specific year.
        """
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        query = db.query(models.Leave).filter(
            models.Leave.employee_id == employee_id,
            models.Leave.start_date <= end_date,
            models.Leave.end_date >= start_date,
        )

        if leave_type:
            query = query.filter(models.Leave.leave_type == leave_type)

        if status:
            query = query.filter(models.Leave.status == status)

        return query.order_by(models.Leave.start_date).all()

    def get_department_leaves_data(
        self,
        db: Session,
        *,
        department_id: str,
        start_date: date,
        end_date: date,
        leave_type: Optional[models.LeaveType] = None,
        status: Optional[models.LeaveStatus] = None,
        employee_ids: Optional[List[str]] = None,
    ) -> List[models.Leave]:
        """
        Fetches leave records for a whole department.
        """
        department = db.query(models.Department).filter(models.Department.id == department_id).first()
        if not department: return []

        return self.get_organization_leaves_data(
            db,
            organization_id=department.organization_id,
            start_date=start_date,
            end_date=end_date,
            leave_type=leave_type,
            status=status,
            department_ids=[department_id],
            employee_ids=employee_ids
        )

    def get_comparative_analysis_data(self, db: Session, *, year: int, organization_ids: List[str], month: Optional[int] = None, quarter: Optional[int] = None) -> List[Dict[str, Any]]:
        if month:
            start_date, end_date = date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
        elif quarter:
            start_month = (quarter - 1) * 3 + 1
            end_month = start_month + 2
            start_date, end_date = date(year, start_month, 1), date(year, end_month, calendar.monthrange(year, end_month)[1])
        else:
            start_date, end_date = date(year, 1, 1), date(year, 12, 31)

        analysis_report = []
        organizations = db.query(models.Organization).filter(models.Organization.id.in_(organization_ids)).all()
        for org in organizations:
            presence_data = self.get_organization_presence_data(db, organization_id=org.id, start_date=start_date, end_date=end_date)
            leaves_data = self.get_organization_leaves_data(db, organization_id=org.id, start_date=start_date, end_date=end_date)

            total_workdays = sum(emp['present_days'] + emp['absent_days'] for emp in presence_data)
            total_present_days = sum(emp['present_days'] for emp in presence_data)
            attendance_rate = (total_present_days / total_workdays * 100) if total_workdays > 0 else 0

            analysis_report.append({
                "organization_name": org.name,
                "attendance_rate": round(attendance_rate, 2),
                "total_hours_worked": sum(emp['total_hours_worked'] for emp in presence_data),
                "total_leave_days": sum((leave.end_date - leave.start_date).days + 1 for leave in leaves_data if leave.status == models.LeaveStatus.APPROVED)
            })
        return analysis_report

    def get_device_usage_data(self, db: Session, *, start_date: date, end_date: date, organization_ids: Optional[List[str]] = None, site_ids: Optional[List[str]] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        # TODO: Implement historical device status tracking.
        # The current Device model only stores the *current* status and does not log historical changes.
        # To implement this feature correctly, a new model like `DeviceStatusLog` is required.
        # This function currently ignores the date parameters and returns the current status of all devices.

        query = db.query(models.Device).options(joinedload(models.Device.site).joinedload(models.Site.organization))

        if organization_ids:
            query = query.join(models.Site).filter(models.Site.organization_id.in_(organization_ids))
        if site_ids:
            query = query.filter(models.Device.site_id.in_(site_ids))
        if status:
            # This filters by the *current* status, not historical.
            query = query.filter(models.Device.status == status.lower())

        devices = query.all()

        return [{
            "device_name": dev.name,
            "device_serial_number": dev.serial_number,
            "site_name": dev.site.name if dev.site else "N/A",
            "organization_name": dev.site.organization.name if dev.site and dev.site.organization else "N/A",
            "status": dev.status.value,
            "last_ping": "N/A" # last_ping is not in the model
        } for dev in devices]

    def get_user_audit_data(self, db: Session, *, organization_ids: Optional[List[str]] = None, role_ids: Optional[List[str]] = None, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        query = db.query(models.User).options(
            joinedload(models.User.role),
            joinedload(models.User.organization)
        )

        if organization_ids:
            query = query.filter(models.User.organization_id.in_(organization_ids))
        if role_ids:
            query = query.filter(models.User.role_id.in_(role_ids))
        if is_active is not None:
            query = query.filter(models.User.is_active == is_active)

        users = query.all()

        return [{
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role.name if user.role else "N/A",
            "organization_name": user.organization.name if user.organization else "N/A",
            "is_active": user.is_active,
            "last_login": user.last_login.isoformat() if user.last_login else "N/A"
        } for user in users]


    def get_anomalies_report_data(self, db: Session, *, organization_id: str, start_date: date, end_date: date, tardiness_threshold: int, site_ids: Optional[List[str]] = None, department_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        query = db.query(models.Employee).options(joinedload(models.Employee.user), joinedload(models.Employee.department)).filter(models.Employee.organization_id == organization_id)
        if site_ids: query = query.filter(models.Employee.site_id.in_(site_ids))
        if department_ids: query = query.filter(models.Employee.department_id.in_(department_ids))

        employees = query.all()
        emp_details = self._get_bulk_employee_presence_details(db, [emp.id for emp in employees], start_date, end_date)

        anomalies = []
        # TODO: Implement shift-based tardiness. This requires a fully implemented Shift model and assignment of shifts to employees.
        # The current logic assumes a fixed 9:00 AM start time for all employees, which is not suitable for production.
        assumed_start_time = timedelta(hours=9)

        for emp in employees:
            daily_data = emp_details.get(emp.id, [])
            for day in daily_data:
                if day['status'] == 'Present':
                    if day['check_in'] and not day['check_out'] and day['date'] < date.today():
                        anomalies.append({
                            "employee_name": emp.user.full_name, "department_name": emp.department.name if emp.department else 'N/A', "date": day['date'],
                            "anomaly_type": "Missing Check-out", "details": f"Checked in at {day['check_in']} but never checked out."
                        })

                    if day['check_in']:
                        h, m, s = map(int, day['check_in'].split(':'))
                        check_in_time = timedelta(hours=h, minutes=m, seconds=s)
                        if (check_in_time - assumed_start_time).total_seconds() / 60 > tardiness_threshold:
                             anomalies.append({
                                "employee_name": emp.user.full_name, "department_name": emp.department.name if emp.department else 'N/A', "date": day['date'],
                                "anomaly_type": "Late Arrival", "details": f"Arrived at {day['check_in']}, {((check_in_time - assumed_start_time).total_seconds() / 60):.0f} minutes late."
                            })
        return anomalies

    def get_payroll_export_data(self, db: Session, *, organization_id: str, year: int, month: int, site_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        _, num_days = calendar.monthrange(year, month)
        start_date, end_date = date(year, month, 1), date(year, month, num_days)

        presence_data = self.get_organization_presence_data(db, organization_id=organization_id, start_date=start_date, end_date=end_date, site_ids=site_ids)
        leaves_data = self.get_organization_leaves_data(db, organization_id=organization_id, start_date=start_date, end_date=end_date)

        leaves_by_employee = {}
        for leave in leaves_data:
            if leave.status == models.LeaveStatus.APPROVED:
                leaves_by_employee.setdefault(leave.employee_id, 0)
                # Correctly calculate leave days that fall within the reporting month
                overlap_start = max(leave.start_date, start_date)
                overlap_end = min(leave.end_date, end_date)
                if overlap_start <= overlap_end:
                    leaves_by_employee[leave.employee_id] += (overlap_end - overlap_start).days + 1

        payroll_data = []
        for emp_data in presence_data:
            # TODO: Implement robust overtime calculation.
            # The current logic assumes a standard 8-hour workday, which is a placeholder.
            # A full implementation requires integrating with a shift and contract management system
            # to determine the correct theoretical hours for each employee.
            workdays = emp_data['present_days'] + emp_data['absent_days']
            theoretical_hours = workdays * 8
            overtime = max(0, emp_data['total_hours_worked'] - theoretical_hours)

            payroll_data.append({
                "employee_id": emp_data['employee_id'],
                "employee_name": emp_data['employee_name'],
                "total_hours_worked": round(emp_data['total_hours_worked'], 2),
                "overtime_hours": round(overtime, 2),
                "leave_days": leaves_by_employee.get(emp_data['employee_id'], 0)
            })
        return payroll_data


    def get_hours_validation_data(self, db: Session, *, department_id: str, year: int, month: int, employee_ids: Optional[List[str]] = None, validation_status: str) -> List[Dict[str, Any]]:
        _, num_days = calendar.monthrange(year, month)
        start_date, end_date = date(year, month, 1), date(year, month, num_days)

        presence_data = self.get_department_presence_data(db, department_id=department_id, start_date=start_date, end_date=end_date, employee_ids=employee_ids)

        # TODO: Implement a full validation workflow.
        # This requires:
        # 1. A new model, e.g., `ValidatedHours`, to store the validation status per employee per period.
        # 2. An API endpoint for managers to submit validations.
        # 3. Filtering logic in this function to use the `validation_status` parameter.
        # The current implementation returns all hours as 'Pending Validation'.
        validation_report = []
        for emp in presence_data:
            validation_report.append({
                "employee_name": emp["employee_name"],
                "total_hours_worked": emp["total_hours_worked"],
                "total_hours_to_validate": emp["total_hours_worked"], # Assuming all worked hours need validation
                "status": "Pending Validation"
            })

        # Here you could filter by status if it were a real field
        # if validation_status == "validated":
        #     return [row for row in validation_report if row['status'] == 'Validated']
        # else:
        #     return [row for row in validation_report if row['status'] == 'Pending Validation']

        return validation_report

report = CRUDReport()