from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import date
from enum import Enum


class ReportFormat(str, Enum):
    """Format de rapport"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class ReportPeriod(str, Enum):
    """Période de rapport"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ReportRequest(BaseModel):
    """Requête de génération de rapport"""
    organization_id: int
    period: ReportPeriod
    start_date: date
    end_date: date
    format: ReportFormat = ReportFormat.PDF
    employee_ids: Optional[List[int]] = None
    department: Optional[str] = None
    include_charts: bool = True


class AttendanceReportRow(BaseModel):
    """Ligne de rapport de présence"""
    employee_id: UUID
    employee_name: str
    badge_id: str
    department: Optional[str] = None
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    on_leave_days: int
    attendance_rate: float
    total_hours: float


class AttendanceReport(BaseModel):
    """Rapport de présence complet"""
    organization_name: str
    period: str
    start_date: date
    end_date: date
    total_employees: int
    rows: List[AttendanceReportRow]
    summary: dict


class EmployeeDetailReport(BaseModel):
    """Rapport détaillé d'un employé"""
    employee_id: UUID
    employee_name: str
    badge_id: str
    department: Optional[str] = None
    period: str
    total_check_ins: int
    total_check_outs: int
    average_arrival_time: Optional[str] = None
    average_departure_time: Optional[str] = None
    late_arrivals: int
    early_departures: int
    total_hours: float
    attendance_rate: float


class EmployeePresenceReportRequest(BaseModel):
    """Request for R17 - Employee Presence Report"""
    start_date: date
    end_date: date
    format: ReportFormat = ReportFormat.PDF
    detailed: bool = False


class EmployeePresenceReportRow(BaseModel):
    """Data row for R17"""
    date: date
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    total_hours: Optional[float] = None
    status: str # e.g., Present, Absent, On Leave


class EmployeePresenceReportResponse(BaseModel):
    """Response for R17 preview"""
    employee_name: str
    employee_badge_id: str
    department_name: Optional[str] = None
    start_date: date
    end_date: date
    data: List[EmployeePresenceReportRow]
    summary: Dict[str, Any]


class EmployeeMonthlySummaryRequest(BaseModel):
    """Request for R18 - Employee Monthly Summary"""
    year: int
    month: int
    include_charts: bool = True # For potential future use


class EmployeeMonthlySummaryResponse(BaseModel):
    """Response for R18 preview and data"""
    employee_name: str
    employee_badge_id: str
    department_name: Optional[str] = None
    period: str
    summary: Dict[str, Any]
    daily_data: List[Dict[str, Any]] # For chart on frontend


from app.models.leave import LeaveStatus, LeaveType

class EmployeeLeavesReportRequest(BaseModel):
    """Request for R19 - Employee Leaves Report"""
    year: int
    leave_type: Optional[LeaveType] = None
    status: Optional[LeaveStatus] = None
    format: ReportFormat = ReportFormat.PDF


class EmployeeLeaveReportRow(BaseModel):
    """Data row for R19"""
    start_date: date
    end_date: date
    leave_type: str
    status: str
    reason: str
    total_days: int

    class Config:
        from_attributes = True


class EmployeeLeavesReportResponse(BaseModel):
    """Response for R19 preview"""
    employee_name: str
    year: int
    data: List[EmployeeLeaveReportRow]
    summary: Dict[str, int]


class PresenceCertificateRequest(BaseModel):
    """Request for R20 - Presence Certificate"""
    start_date: date
    end_date: date


# Schemas for Manager Reports (Phase 2)

class DepartmentPresenceRequest(BaseModel):
    """Request for R12 - Department Presence Report"""
    start_date: date
    end_date: date
    employee_ids: Optional[List[str]] = None # Filter by specific employees in department
    format: ReportFormat = ReportFormat.PDF
    grouping: str = "daily" # daily, weekly


class DepartmentPresenceReportRow(BaseModel):
    """Data row for R12, one row per employee"""
    employee_id: str
    employee_name: str
    present_days: int
    absent_days: int
    on_leave_days: int
    total_hours_worked: float


class DepartmentPresenceResponse(BaseModel):
    """Response for R12 preview"""
    department_name: str
    period: str
    data: List[DepartmentPresenceReportRow]
    summary: Dict[str, Any]


class TeamWeeklyReportRequest(BaseModel):
    """Request for R13 - Team Weekly Report"""
    year: int
    week_number: int
    format: ReportFormat = ReportFormat.PDF
    detailed: bool = False # Synthèse vs Détaillé


class DepartmentLeavesRequest(BaseModel):
    """Request for R15 - Department Leaves Report"""
    start_date: date
    end_date: date
    leave_type: Optional[LeaveType] = None
    status: Optional[LeaveStatus] = None
    employee_ids: Optional[List[str]] = None
    format: ReportFormat = ReportFormat.PDF


class DepartmentLeaveReportRow(BaseModel):
    """Data row for R15"""
    employee_name: str
    start_date: date
    end_date: date
    leave_type: str
    status: str
    reason: str
    total_days: int


class DepartmentLeavesResponse(BaseModel):
    """Response for R15 preview"""
    department_name: str
    period: str
    data: List[DepartmentLeaveReportRow]


class TeamPerformanceRequest(BaseModel):
    """Request for R16 - Team Performance Report"""
    year: int
    month: Optional[int] = None
    quarter: Optional[int] = None
    format: ReportFormat = ReportFormat.PDF


class TeamPerformanceRow(BaseModel):
    """Data row for R16"""
    employee_id: str
    employee_name: str
    attendance_rate: float
    total_hours_worked: float
    # punctuality_score: Optional[float] = None # To be added later


class TeamPerformanceResponse(BaseModel):
    """Response for R16 preview"""
    department_name: str
    period: str
    data: List[TeamPerformanceRow]


# Schemas for HR / Org Admin Reports (Phase 3)

class OrganizationPresenceRequest(BaseModel):
    """Request for R5 - Organization Presence Report"""
    start_date: date
    end_date: date
    site_ids: Optional[List[str]] = None
    department_ids: Optional[List[str]] = None
    format: ReportFormat = ReportFormat.PDF


class OrganizationPresenceResponse(BaseModel):
    """Response for R5 preview"""
    organization_name: str
    period: str
    data: List[DepartmentPresenceReportRow] # Reusing the row schema from R12
    summary: Dict[str, Any]


class MonthlySyntheticReportRequest(BaseModel):
    """Request for R6 - Monthly Synthetic Report"""
    year: int
    month: int
    site_ids: Optional[List[str]] = None
    department_ids: Optional[List[str]] = None
    include_overtime: bool = True
    format: ReportFormat = ReportFormat.PDF


class OrganizationLeavesRequest(BaseModel):
    """Request for R7 - Organization Leaves Analysis"""
    start_date: date
    end_date: date
    leave_type: Optional[LeaveType] = None
    status: Optional[LeaveStatus] = None
    department_ids: Optional[List[str]] = None
    employee_ids: Optional[List[str]] = None
    format: ReportFormat = ReportFormat.PDF


class WorkedHoursRequest(BaseModel):
    """Request for R9 - Worked Hours per Employee Report"""
    start_date: date
    end_date: date
    department_ids: Optional[List[str]] = None
    employee_ids: Optional[List[str]] = None
    format: ReportFormat = ReportFormat.PDF


class WorkedHoursRow(BaseModel):
    """Data row for R9"""
    employee_name: str
    department_name: Optional[str]
    date: date
    status: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    total_hours: float


class WorkedHoursResponse(BaseModel):
    """Response for R9 preview"""
    organization_name: str
    period: str
    data: List[WorkedHoursRow]


class SiteActivityRequest(BaseModel):
    """Request for R10 - Site Activity Report"""
    start_date: date
    end_date: date
    site_ids: List[str]
    format: ReportFormat = ReportFormat.PDF
    detailed: bool = False


class SiteActivityRow(BaseModel):
    """Data row for R10"""
    site_name: str
    total_employees: int
    present_employees: int
    on_leave_employees: int
    total_hours_worked: float
    average_hours_per_employee: float


class SiteActivityResponse(BaseModel):
    """Response for R10 preview"""
    organization_name: str
    period: str
    data: List[SiteActivityRow]


# Schemas for Super Admin Reports (Phase 4)

class MultiOrgConsolidatedRequest(BaseModel):
    """Request for R1 - Multi-Organization Consolidated Report"""
    start_date: date
    end_date: date
    organization_ids: Optional[List[str]] = None
    metric_type: str # 'presence', 'leaves', 'delays'
    grouping: str # 'daily', 'weekly', 'monthly'
    format: ReportFormat = ReportFormat.PDF


class MultiOrgConsolidatedRow(BaseModel):
    """Data row for R1"""
    organization_name: str
    present_days: int
    on_leave_days: int
    # late_days: int # Deferred
    total_hours_worked: float


class MultiOrgConsolidatedResponse(BaseModel):
    """Response for R1 preview"""
    period: str
    data: List[MultiOrgConsolidatedRow]