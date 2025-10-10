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