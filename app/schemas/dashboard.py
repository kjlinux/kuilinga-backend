from pydantic import BaseModel
from typing import List, Dict

# System Administrator Schemas
class UsersPerOrg(BaseModel):
    name: str
    user_count: int

class SitesPerOrg(BaseModel):
    name: str
    site_count: int

class DeviceStatusRatio(BaseModel):
    status: str
    count: int

class PlanDistribution(BaseModel):
    plan: str
    count: int

class Top10Organizations(BaseModel):
    name: str
    employee_count: int

class AdminDashboard(BaseModel):
    active_organizations: int
    users_per_organization: List[UsersPerOrg]
    sites_per_organization: List[SitesPerOrg]
    device_status_ratio: List[DeviceStatusRatio]
    daily_attendance_count: int
    plan_distribution: List[PlanDistribution]
    top_10_organizations_by_employees: List[Top10Organizations]

# Manager/HR Schemas
from .attendance import Attendance

from datetime import date

class PresenceEvolution(BaseModel):
    date: date
    presence_count: int

class PresenceAbsenceTardinessDistribution(BaseModel):
    present: int
    absent: int
    tardy: int

class ManagerDashboard(BaseModel):
    present_today: int
    absent_today: int
    tardy_today: int
    attendance_rate: float
    total_work_hours: float
    pending_leaves: int
    presence_evolution: List[PresenceEvolution]
    presence_absence_tardiness_distribution: PresenceAbsenceTardinessDistribution
    real_time_attendances: List[Attendance]

# Employee Schemas
class LeaveBalance(BaseModel):
    total: int
    used: int
    available: int

class EmployeeDashboard(BaseModel):
    today_attendances: List[Attendance]
    monthly_attendance_rate: float
    leave_balance: LeaveBalance

# Integrator/IoT Technician Schemas
class AttendancePerDevice(BaseModel):
    serial_number: str
    attendance_count: int

class IntegratorDashboard(BaseModel):
    device_status_ratio: List[DeviceStatusRatio]
    attendance_per_device: List[AttendancePerDevice]

# Advanced Analytics Schemas
class TardinessByDay(BaseModel):
    day: str
    tardy_count: int

class AdvancedAnalytics(BaseModel):
    tardiness_by_day_of_week: List[TardinessByDay]