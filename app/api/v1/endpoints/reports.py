from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, crud
from app.dependencies import (
    get_db,
    get_current_active_user,
    get_current_active_employee,
    get_current_active_manager,
    get_current_active_superuser,
    require_role,
)
from app.services.reporting_service import reporting_service
from typing import Any, Dict
from datetime import date, timedelta
import calendar

router = APIRouter()


#
# Reports for Employees (R17-R20)
#

# R17
def _get_r17_data(db: Session, report_in: schemas.EmployeePresenceReportRequest, current_employee: models.Employee) -> Dict[str, Any]:
    report_data = crud.report.get_employee_presence_data(db, employee_id=current_employee.id, start_date=report_in.start_date, end_date=report_in.end_date)
    if not report_data: raise HTTPException(status_code=404, detail="No attendance data found for the selected period.")
    summary = {"total_days": len(report_data), "present_days": sum(1 for r in report_data if r["status"] == "Present"), "absent_days": sum(1 for r in report_data if r["status"] == "Absent"), "on_leave_days": sum(1 for r in report_data if r["status"] == "On Leave"), "total_hours_worked": sum(r.get("total_hours", 0) for r in report_data)}
    return {"employee_name": current_employee.user.full_name, "employee_badge_id": current_employee.badge_id, "department_name": current_employee.department.name if current_employee.department else None, "start_date": report_in.start_date, "end_date": report_in.end_date, "data": report_data, "summary": summary}

@router.post("/employee/presence/preview", response_model=schemas.EmployeePresenceReportResponse, summary="R17 - Preview My Presence Report", tags=["Reports - Employee"])
def preview_employee_presence_report(*, db: Session = Depends(get_db), report_in: schemas.EmployeePresenceReportRequest, current_employee: models.Employee = Depends(get_current_active_employee)):
    return _get_r17_data(db, report_in, current_employee)

@router.post("/employee/presence/download", summary="R17 - Download My Presence Report", tags=["Reports - Employee"])
async def download_employee_presence_report(*, db: Session = Depends(get_db), report_in: schemas.EmployeePresenceReportRequest, current_employee: models.Employee = Depends(get_current_active_employee)):
    response_data = _get_r17_data(db, report_in, current_employee)
    filename = f"R17_Presence_{current_employee.id}_{report_in.start_date}_to_{report_in.end_date}.{report_in.format.value}"
    context = {"report_title": "Mon Relevé de Présence", "period": f"Du {report_in.start_date.strftime('%d/%m/%Y')} au {report_in.end_date.strftime('%d/%m/%Y')}", **response_data}
    if report_in.format == schemas.ReportFormat.PDF: return await reporting_service.generate_pdf_from_html("reports/r17_employee_presence.html", context, filename)
    elif report_in.format == schemas.ReportFormat.CSV: return await reporting_service.generate_csv(response_data["data"], filename)
    else: raise HTTPException(status_code=400, detail="Format not supported for this report. Please choose PDF or CSV.")

# R18
def _get_r18_data(db: Session, report_in: schemas.EmployeeMonthlySummaryRequest, current_employee: models.Employee) -> Dict[str, Any]:
    report_data = crud.report.get_employee_monthly_summary_data(db, employee_id=current_employee.id, year=report_in.year, month=report_in.month)
    if not report_data: raise HTTPException(status_code=404, detail="No data found for the selected month.")
    return {"employee_name": current_employee.user.full_name, "employee_badge_id": current_employee.badge_id, "department_name": current_employee.department.name if current_employee.department else None, **report_data}

@router.post("/employee/monthly-summary/preview", response_model=schemas.EmployeeMonthlySummaryResponse, summary="R18 - Preview My Monthly Summary", tags=["Reports - Employee"])
def preview_employee_monthly_summary(*, db: Session = Depends(get_db), report_in: schemas.EmployeeMonthlySummaryRequest, current_employee: models.Employee = Depends(get_current_active_employee)):
    return _get_r18_data(db, report_in, current_employee)

@router.post("/employee/monthly-summary/download", summary="R18 - Download My Monthly Summary", tags=["Reports - Employee"])
async def download_employee_monthly_summary(*, db: Session = Depends(get_db), report_in: schemas.EmployeeMonthlySummaryRequest, current_employee: models.Employee = Depends(get_current_active_employee)):
    response_data = _get_r18_data(db, report_in, current_employee)
    filename = f"R18_MonthlySummary_{current_employee.id}_{report_in.year}-{report_in.month}.pdf"
    context = {"report_title": "Mon Récapitulatif Mensuel", "daily_data_json": [d["hours"] for d in response_data["daily_data"]], **response_data}
    return await reporting_service.generate_pdf_from_html("reports/r18_employee_monthly.html", context, filename)

# R19
def _get_r19_data(db: Session, report_in: schemas.EmployeeLeavesReportRequest, current_employee: models.Employee) -> Dict[str, Any]:
    leaves = crud.report.get_employee_leaves_data(db, employee_id=current_employee.id, year=report_in.year, leave_type=report_in.leave_type, status=report_in.status)
    report_data, summary = [], {"total": 0, "approved": 0, "pending": 0, "rejected": 0}
    for leave in leaves:
        duration = (leave.end_date - leave.start_date).days + 1
        report_data.append(schemas.EmployeeLeaveReportRow(start_date=leave.start_date, end_date=leave.end_date, leave_type=leave.leave_type.value, status=leave.status.value, reason=leave.reason, total_days=duration))
        if leave.status == models.LeaveStatus.APPROVED: summary["approved"] += duration
        elif leave.status == models.LeaveStatus.PENDING: summary["pending"] += duration
        elif leave.status == models.LeaveStatus.REJECTED: summary["rejected"] += duration
        summary["total"] += duration
    return {"employee_name": current_employee.user.full_name, "year": report_in.year, "data": report_data, "summary": summary}

@router.post("/employee/leaves/preview", response_model=schemas.EmployeeLeavesReportResponse, summary="R19 - Preview My Leaves Report", tags=["Reports - Employee"])
def preview_employee_leaves_report(*, db: Session = Depends(get_db), report_in: schemas.EmployeeLeavesReportRequest, current_employee: models.Employee = Depends(get_current_active_employee)):
    return _get_r19_data(db, report_in, current_employee)

@router.post("/employee/leaves/download", summary="R19 - Download My Leaves Report", tags=["Reports - Employee"])
async def download_employee_leaves_report(*, db: Session = Depends(get_db), report_in: schemas.EmployeeLeavesReportRequest, current_employee: models.Employee = Depends(get_current_active_employee)):
    response_data = _get_r19_data(db, report_in, current_employee)
    report_data_dict = [row.model_dump() for row in response_data["data"]]
    if not report_data_dict: raise HTTPException(status_code=404, detail="No leave data found for the selected criteria.")
    filename = f"R19_Leaves_{current_employee.id}_{report_in.year}.{report_in.format.value}"
    context = {"report_title": f"Rapport de Congés {report_in.year}", "data": report_data_dict, **response_data}
    if report_in.format == schemas.ReportFormat.PDF: return await reporting_service.generate_pdf_from_html("reports/r19_employee_leaves.html", context, filename)
    elif report_in.format == schemas.ReportFormat.EXCEL: return await reporting_service.generate_excel(report_data_dict, filename)
    else: raise HTTPException(status_code=400, detail="Format not supported. Please choose PDF or Excel.")

# R20
@router.post("/employee/presence-certificate/download", summary="R20 - Download My Presence Certificate", tags=["Reports - Employee"])
async def download_presence_certificate(*, db: Session = Depends(get_db), report_in: schemas.PresenceCertificateRequest, current_employee: models.Employee = Depends(get_current_active_employee)):
    report_data = crud.report.get_employee_presence_data(db, employee_id=current_employee.id, start_date=report_in.start_date, end_date=report_in.end_date)
    if not report_data: raise HTTPException(status_code=404, detail="No attendance data found for the selected period.")
    present_days = sum(1 for row in report_data if row["status"] == "Present")
    total_days = (report_in.end_date - report_in.start_date).days + 1
    filename = f"R20_Attestation_{current_employee.id}_{report_in.start_date}_to_{report_in.end_date}.pdf"
    context = {"report_title": "Attestation de Présence", "employee_name": current_employee.user.full_name, "employee_badge_id": current_employee.badge_id, "organization_name": current_employee.organization.name, "start_date": report_in.start_date, "end_date": report_in.end_date, "present_days": present_days, "total_days_in_period": total_days, "issue_date": date.today()}
    return await reporting_service.generate_pdf_from_html("reports/r20_presence_certificate.html", context, filename)

#
# Reports for Managers (R12-R16)
#

# R12
def _get_r12_data(db: Session, report_in: schemas.DepartmentPresenceRequest, current_manager: models.Employee) -> Dict[str, Any]:
    report_data = crud.report.get_department_presence_data(db, department_id=current_manager.department_id, start_date=report_in.start_date, end_date=report_in.end_date, employee_ids=report_in.employee_ids)
    if not report_data: raise HTTPException(status_code=404, detail="No attendance data found for the department in this period.")
    summary = {"total_employees": len(report_data), "total_hours": sum(r["total_hours_worked"] for r in report_data), "average_hours_per_employee": (sum(r["total_hours_worked"] for r in report_data) / len(report_data)) if report_data else 0}
    return {"department_name": current_manager.department.name, "period": f"{report_in.start_date.strftime('%d/%m/%Y')} - {report_in.end_date.strftime('%d/%m/%Y')}", "data": report_data, "summary": summary}

@router.post("/manager/department-presence/preview", response_model=schemas.DepartmentPresenceResponse, summary="R12 - Preview Department Presence Report", tags=["Reports - Manager"])
def preview_department_presence_report(*, db: Session = Depends(get_db), report_in: schemas.DepartmentPresenceRequest, current_manager: models.Employee = Depends(get_current_active_manager)):
    return _get_r12_data(db, report_in, current_manager)

@router.post("/manager/department-presence/download", summary="R12 - Download Department Presence Report", tags=["Reports - Manager"])
async def download_department_presence_report(*, db: Session = Depends(get_db), report_in: schemas.DepartmentPresenceRequest, current_manager: models.Employee = Depends(get_current_active_manager)):
    response_data = _get_r12_data(db, report_in, current_manager)
    filename = f"R12_DeptPresence_{current_manager.department.name}_{report_in.start_date}_to_{report_in.end_date}.{report_in.format.value}"
    context = {"report_title": f"Rapport de Présence - Département {current_manager.department.name}", "total_employees": len(response_data["data"]), **response_data}
    if report_in.format == schemas.ReportFormat.PDF: return await reporting_service.generate_pdf_from_html("reports/r12_department_presence.html", context, filename)
    elif report_in.format == schemas.ReportFormat.EXCEL: return await reporting_service.generate_excel(response_data["data"], filename)
    elif report_in.format == schemas.ReportFormat.CSV: return await reporting_service.generate_csv(response_data["data"], filename)
    else: raise HTTPException(status_code=400, detail="Unsupported format")

# R13
def _get_r13_data(db: Session, report_in: schemas.TeamWeeklyReportRequest, current_manager: models.Employee) -> Dict[str, Any]:
    start_of_week = date.fromisocalendar(report_in.year, report_in.week_number, 1)
    end_of_week = start_of_week + timedelta(days=6)
    report_data = crud.report.get_department_presence_data(db, department_id=current_manager.department_id, start_date=start_of_week, end_date=end_of_week)
    if not report_data: raise HTTPException(status_code=404, detail="No attendance data found for the selected week.")
    summary = {"total_employees": len(report_data), "total_hours": sum(r["total_hours_worked"] for r in report_data), "average_hours_per_employee": (sum(r["total_hours_worked"] for r in report_data) / len(report_data)) if report_data else 0}
    return {"department_name": current_manager.department.name, "period": f"Semaine {report_in.week_number}, {report_in.year}", "start_of_week": start_of_week, "end_of_week": end_of_week, "data": report_data, "summary": summary}

@router.post("/manager/team-weekly/preview", response_model=schemas.DepartmentPresenceResponse, summary="R13 - Preview Team Weekly Report", tags=["Reports - Manager"])
def preview_team_weekly_report(*, db: Session = Depends(get_db), report_in: schemas.TeamWeeklyReportRequest, current_manager: models.Employee = Depends(get_current_active_manager)):
    return _get_r13_data(db, report_in, current_manager)

@router.post("/manager/team-weekly/download", summary="R13 - Download Team Weekly Report", tags=["Reports - Manager"])
async def download_team_weekly_report(*, db: Session = Depends(get_db), report_in: schemas.TeamWeeklyReportRequest, current_manager: models.Employee = Depends(get_current_active_manager)):
    response_data = _get_r13_data(db, report_in, current_manager)
    filename = f"R13_Weekly_{current_manager.department.name}_Y{report_in.year}W{report_in.week_number}.{report_in.format.value}"
    context = {"report_title": f"Rapport Hebdomadaire - Département {current_manager.department.name}", "period": f"Semaine {report_in.week_number} ({response_data['start_of_week'].strftime('%d/%m/%Y')} - {response_data['end_of_week'].strftime('%d/%m/%Y')})", "total_employees": len(response_data["data"]), **response_data}
    if report_in.format == schemas.ReportFormat.PDF: return await reporting_service.generate_pdf_from_html("reports/r12_department_presence.html", context, filename)
    elif report_in.format == schemas.ReportFormat.EXCEL: return await reporting_service.generate_excel(response_data["data"], filename)
    else: raise HTTPException(status_code=400, detail="Unsupported format. Please choose PDF or Excel.")


# R14
def _get_r14_data(db: Session, report_in: schemas.HoursValidationRequest, current_manager: models.Employee) -> Dict[str, Any]:
    report_data = crud.report.get_hours_validation_data(
        db,
        department_id=current_manager.department_id,
        year=report_in.year,
        month=report_in.month,
        employee_ids=report_in.employee_ids,
        validation_status=report_in.validation_status
    )
    if not report_data:
        raise HTTPException(status_code=404, detail="No hours data found for the selected period.")

    period_str = f"{calendar.month_name[report_in.month]} {report_in.year}"
    return {
        "department_name": current_manager.department.name,
        "period": period_str,
        "data": report_data
    }

@router.post("/manager/hours-validation/preview", response_model=schemas.HoursValidationResponse, summary="R14 - Preview Hours Validation Report", tags=["Reports - Manager"])
def preview_hours_validation_report(*, db: Session = Depends(get_db), report_in: schemas.HoursValidationRequest, current_manager: models.Employee = Depends(get_current_active_manager)):
    return _get_r14_data(db, report_in, current_manager)

@router.post("/manager/hours-validation/download", summary="R14 - Download Hours Validation Report", tags=["Reports - Manager"])
async def download_hours_validation_report(*, db: Session = Depends(get_db), report_in: schemas.HoursValidationRequest, current_manager: models.Employee = Depends(get_current_active_manager)):
    response_data = _get_r14_data(db, report_in, current_manager)
    filename = f"R14_HoursValidation_{current_manager.department.name}_{response_data['period']}.{report_in.format.value}"
    context = {"report_title": "Validation des Heures", **response_data}

    if report_in.format == schemas.ReportFormat.PDF:
        return await reporting_service.generate_pdf_from_html("reports/r14_hours_validation.html", context, filename)
    elif report_in.format == schemas.ReportFormat.EXCEL:
        return await reporting_service.generate_excel(response_data["data"], filename)
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Please choose PDF or Excel.")


# R8
def _get_r8_data(db: Session, report_in: schemas.AnomaliesReportRequest, current_user: models.User) -> Dict[str, Any]:
    report_data = crud.report.get_anomalies_report_data(
        db,
        organization_id=current_user.organization_id,
        start_date=report_in.start_date,
        end_date=report_in.end_date,
        tardiness_threshold=report_in.tardiness_threshold,
        site_ids=report_in.site_ids,
        department_ids=report_in.department_ids,
    )
    if not report_data:
        raise HTTPException(status_code=404, detail="No anomalies found for the selected criteria.")
    return {
        "organization_name": current_user.organization.name,
        "period": f"{report_in.start_date.strftime('%d/%m/%Y')} - {report_in.end_date.strftime('%d/%m/%Y')}",
        "data": report_data
    }

@router.post("/organization/anomalies/preview", response_model=schemas.AnomaliesReportResponse, summary="R8 - Preview Anomalies Report", tags=["Reports - Organization"], dependencies=[Depends(require_role("admin"))])
def preview_anomalies_report(*, db: Session = Depends(get_db), report_in: schemas.AnomaliesReportRequest, current_user: models.User = Depends(get_current_active_user)):
    if not current_user.organization_id:
        raise HTTPException(status_code=403, detail="User not associated with an organization.")
    return _get_r8_data(db, report_in, current_user)

@router.post("/organization/anomalies/download", summary="R8 - Download Anomalies Report", tags=["Reports - Organization"], dependencies=[Depends(require_role("admin"))])
async def download_anomalies_report(*, db: Session = Depends(get_db), report_in: schemas.AnomaliesReportRequest, current_user: models.User = Depends(get_current_active_user)):
    if not current_user.organization_id:
        raise HTTPException(status_code=403, detail="User not associated with an organization.")
    response_data = _get_r8_data(db, report_in, current_user)
    filename = f"R08_Anomalies_{current_user.organization.name}_{report_in.start_date}_to_{report_in.end_date}.{report_in.format.value}"
    context = {"report_title": "Rapport des Retards et Anomalies", **response_data}
    if report_in.format == schemas.ReportFormat.PDF:
        return await reporting_service.generate_pdf_from_html("reports/r08_anomalies.html", context, filename)
    elif report_in.format in [schemas.ReportFormat.EXCEL, schemas.ReportFormat.CSV]:
        return await reporting_service.generate_excel(response_data["data"], filename) if report_in.format == schemas.ReportFormat.EXCEL else await reporting_service.generate_csv(response_data["data"], filename)
    else:
        raise HTTPException(status_code=400, detail="Unsupported format.")

# R11
@router.post("/organization/payroll-export/download", summary="R11 - Download Payroll Export", tags=["Reports - Organization"], dependencies=[Depends(require_role("admin"))])
async def download_payroll_export(*, db: Session = Depends(get_db), report_in: schemas.PayrollExportRequest, current_user: models.User = Depends(get_current_active_user)):
    if not current_user.organization_id:
        raise HTTPException(status_code=403, detail="User not associated with an organization.")

    report_data = crud.report.get_payroll_export_data(
        db,
        organization_id=current_user.organization_id,
        year=report_in.year,
        month=report_in.month,
        site_ids=report_in.site_ids
    )
    if not report_data:
        raise HTTPException(status_code=404, detail="No data available for payroll export.")

    period = f"{report_in.year}-{report_in.month:02d}"
    filename = f"R11_PayrollExport_{current_user.organization.name}_{period}.{report_in.format.value}"

    if report_in.format == schemas.ReportFormat.EXCEL:
        return await reporting_service.generate_excel(report_data, filename)
    elif report_in.format == schemas.ReportFormat.CSV:
        return await reporting_service.generate_csv(report_data, filename)
    else:
        raise HTTPException(status_code=400, detail="Unsupported format for payroll export. Please choose Excel or CSV.")

# R15
def _get_r15_data(db: Session, report_in: schemas.DepartmentLeavesRequest, current_manager: models.Employee) -> Dict[str, Any]:
    leaves = crud.report.get_department_leaves_data(db, department_id=current_manager.department_id, start_date=report_in.start_date, end_date=report_in.end_date, leave_type=report_in.leave_type, status=report_in.status, employee_ids=report_in.employee_ids)
    report_data = [{"employee_name": l.employee.user.full_name, "start_date": l.start_date, "end_date": l.end_date, "leave_type": l.leave_type.value, "status": l.status.value, "reason": l.reason, "total_days": (l.end_date - l.start_date).days + 1} for l in leaves]
    return {"department_name": current_manager.department.name, "period": f"{report_in.start_date.strftime('%d/%m/%Y')} - {report_in.end_date.strftime('%d/%m/%Y')}", "data": report_data}

@router.post("/manager/department-leaves/preview", response_model=schemas.DepartmentLeavesResponse, summary="R15 - Preview Department Leave Requests", tags=["Reports - Manager"])
def preview_department_leaves_report(*, db: Session = Depends(get_db), report_in: schemas.DepartmentLeavesRequest, current_manager: models.Employee = Depends(get_current_active_manager)):
    return _get_r15_data(db, report_in, current_manager)

@router.post("/manager/department-leaves/download", summary="R15 - Download Department Leave Requests", tags=["Reports - Manager"])
async def download_department_leaves_report(*, db: Session = Depends(get_db), report_in: schemas.DepartmentLeavesRequest, current_manager: models.Employee = Depends(get_current_active_manager)):
    response_data = _get_r15_data(db, report_in, current_manager)
    if not response_data["data"]: raise HTTPException(status_code=404, detail="No leave data found for the selected criteria.")
    filename = f"R15_DeptLeaves_{current_manager.department.name}_{report_in.start_date}_to_{report_in.end_date}.{report_in.format.value}"
    context = {"report_title": f"Rapport des Congés - {current_manager.department.name}", **response_data}
    if report_in.format == schemas.ReportFormat.PDF: return await reporting_service.generate_pdf_from_html("reports/r15_department_leaves.html", context, filename)
    elif report_in.format == schemas.ReportFormat.EXCEL: return await reporting_service.generate_excel(response_data["data"], filename)
    else: raise HTTPException(status_code=400, detail="Unsupported format. Please choose PDF or Excel.")

# R16
def _get_date_range_from_performance_request(report_in: schemas.TeamPerformanceRequest) -> (date, date, str):
    if report_in.month:
        _, num_days = calendar.monthrange(report_in.year, report_in.month)
        start_date, end_date = date(report_in.year, report_in.month, 1), date(report_in.year, report_in.month, num_days)
        period_str = start_date.strftime("%B %Y")
    elif report_in.quarter:
        start_month = (report_in.quarter - 1) * 3 + 1
        end_month, end_day = start_month + 2, calendar.monthrange(report_in.year, start_month + 2)[1]
        start_date, end_date = date(report_in.year, start_month, 1), date(report_in.year, end_month, end_day)
        period_str = f"Q{report_in.quarter} {report_in.year}"
    else:
        start_date, end_date = date(report_in.year, 1, 1), date(report_in.year, 12, 31)
        period_str = f"Année {report_in.year}"
    return start_date, end_date, period_str

def _get_r16_data(db: Session, report_in: schemas.TeamPerformanceRequest, current_manager: models.Employee) -> Dict[str, Any]:
    start_date, end_date, period_str = _get_date_range_from_performance_request(report_in)
    report_data = crud.report.get_team_performance_data(db, department_id=current_manager.department_id, start_date=start_date, end_date=end_date)
    if not report_data: raise HTTPException(status_code=404, detail="No performance data could be generated for the selected period.")
    return {"department_name": current_manager.department.name, "period": period_str, "data": report_data}

@router.post("/manager/team-performance/preview", response_model=schemas.TeamPerformanceResponse, summary="R16 - Preview Team Performance Report", tags=["Reports - Manager"])
def preview_team_performance_report(*, db: Session = Depends(get_db), report_in: schemas.TeamPerformanceRequest, current_manager: models.Employee = Depends(get_current_active_manager)):
    return _get_r16_data(db, report_in, current_manager)

@router.post("/manager/team-performance/download", summary="R16 - Download Team Performance Report", tags=["Reports - Manager"])
async def download_team_performance_report(*, db: Session = Depends(get_db), report_in: schemas.TeamPerformanceRequest, current_manager: models.Employee = Depends(get_current_active_manager)):
    response_data = _get_r16_data(db, report_in, current_manager)
    filename = f"R16_TeamPerf_{current_manager.department.name}_{response_data['period']}.{report_in.format.value}"
    context = {"report_title": f"Rapport de Performance - {current_manager.department.name}", **response_data}
    if report_in.format == schemas.ReportFormat.PDF: return await reporting_service.generate_pdf_from_html("reports/r16_team_performance.html", context, filename)
    elif report_in.format == schemas.ReportFormat.EXCEL: return await reporting_service.generate_excel(response_data["data"], filename)
    else: raise HTTPException(status_code=400, detail="Unsupported format. Please choose PDF or Excel.")

#
# Reports for HR / Org Admins (R5-R11)
#

# R5
def _get_r5_data(db: Session, report_in: schemas.OrganizationPresenceRequest, current_user: models.User) -> Dict[str, Any]:
    report_data = crud.report.get_organization_presence_data(db, organization_id=current_user.organization_id, start_date=report_in.start_date, end_date=report_in.end_date, site_ids=report_in.site_ids, department_ids=report_in.department_ids)
    if not report_data: raise HTTPException(status_code=404, detail="No attendance data found for the organization in this period.")
    summary = {"total_employees": len(report_data), "total_hours": sum(r["total_hours_worked"] for r in report_data)}
    return {"organization_name": current_user.organization.name, "period": f"{report_in.start_date.strftime('%d/%m/%Y')} - {report_in.end_date.strftime('%d/%m/%Y')}", "data": report_data, "summary": summary}

@router.post("/organization/presence/preview", response_model=schemas.OrganizationPresenceResponse, summary="R5 - Preview Organization Presence Report", tags=["Reports - Organization"], dependencies=[Depends(require_role("admin"))])
def preview_organization_presence_report(*, db: Session = Depends(get_db), report_in: schemas.OrganizationPresenceRequest, current_user: models.User = Depends(get_current_active_user)):
    if not current_user.organization_id: raise HTTPException(status_code=403, detail="User not associated with an organization.")
    return _get_r5_data(db, report_in, current_user)

@router.post("/organization/presence/download", summary="R5 - Download Organization Presence Report", tags=["Reports - Organization"], dependencies=[Depends(require_role("admin"))])
async def download_organization_presence_report(*, db: Session = Depends(get_db), report_in: schemas.OrganizationPresenceRequest, current_user: models.User = Depends(get_current_active_user)):
    if not current_user.organization_id: raise HTTPException(status_code=403, detail="User not associated with an organization.")
    response_data = _get_r5_data(db, report_in, current_user)
    filename = f"R05_OrgPresence_{current_user.organization.name}_{report_in.start_date}_to_{report_in.end_date}.{report_in.format.value}"
    context = {"report_title": f"Rapport de Présence - {current_user.organization.name}", **response_data}
    if report_in.format == schemas.ReportFormat.PDF: return await reporting_service.generate_pdf_from_html("reports/r05_organization_presence.html", context, filename)
    elif report_in.format == schemas.ReportFormat.EXCEL: return await reporting_service.generate_excel(response_data["data"], filename)
    elif report_in.format == schemas.ReportFormat.CSV: return await reporting_service.generate_csv(response_data["data"], filename)
    else: raise HTTPException(status_code=400, detail="Unsupported format")

# R6
def _get_r6_data(db: Session, report_in: schemas.MonthlySyntheticReportRequest, current_user: models.User) -> Dict[str, Any]:
    _, num_days = calendar.monthrange(report_in.year, report_in.month)
    start_date, end_date = date(report_in.year, report_in.month, 1), date(report_in.year, report_in.month, num_days)
    report_data = crud.report.get_organization_presence_data(db, organization_id=current_user.organization_id, start_date=start_date, end_date=end_date, site_ids=report_in.site_ids, department_ids=report_in.department_ids)
    if not report_data: raise HTTPException(status_code=404, detail="No data found for the selected month.")
    summary = {"total_employees": len(report_data), "total_present_days": sum(r["present_days"] for r in report_data), "total_absent_days": sum(r["absent_days"] for r in report_data), "total_on_leave_days": sum(r["on_leave_days"] for r in report_data), "total_hours_worked": sum(r["total_hours_worked"] for r in report_data)}
    return {"organization_name": current_user.organization.name, "period": start_date.strftime("%B %Y"), "data": report_data, "summary": summary}

@router.post("/organization/monthly-synthetic/preview", response_model=schemas.OrganizationPresenceResponse, summary="R6 - Preview Monthly Synthetic Report", tags=["Reports - Organization"], dependencies=[Depends(require_role("admin"))])
def preview_monthly_synthetic_report(*, db: Session = Depends(get_db), report_in: schemas.MonthlySyntheticReportRequest, current_user: models.User = Depends(get_current_active_user)):
    if not current_user.organization_id: raise HTTPException(status_code=403, detail="User not associated with an organization.")
    return _get_r6_data(db, report_in, current_user)

@router.post("/organization/monthly-synthetic/download", summary="R6 - Download Monthly Synthetic Report", tags=["Reports - Organization"], dependencies=[Depends(require_role("admin"))])
async def download_monthly_synthetic_report(*, db: Session = Depends(get_db), report_in: schemas.MonthlySyntheticReportRequest, current_user: models.User = Depends(get_current_active_user)):
    if not current_user.organization_id: raise HTTPException(status_code=403, detail="User not associated with an organization.")
    response_data = _get_r6_data(db, report_in, current_user)
    filename = f"R06_MonthlySynthetic_{current_user.organization.name}_{response_data['period']}.{report_in.format.value}"
    context = {"report_title": f"Rapport Mensuel Synthétique - {response_data['period']}", **response_data}
    if report_in.format == schemas.ReportFormat.PDF: return await reporting_service.generate_pdf_from_html("reports/r06_monthly_synthetic.html", context, filename)
    elif report_in.format == schemas.ReportFormat.EXCEL: return await reporting_service.generate_excel(response_data["data"], filename)
    else: raise HTTPException(status_code=400, detail="Unsupported format")

# R7
def _get_r7_data(db: Session, report_in: schemas.OrganizationLeavesRequest, current_user: models.User) -> Dict[str, Any]:
    leaves = crud.report.get_organization_leaves_data(db, organization_id=current_user.organization_id, start_date=report_in.start_date, end_date=report_in.end_date, leave_type=report_in.leave_type, status=report_in.status, department_ids=report_in.department_ids, employee_ids=report_in.employee_ids)
    report_data = [{"employee_name": l.employee.user.full_name, "department_name": l.employee.department.name if l.employee.department else 'N/A', "start_date": l.start_date, "end_date": l.end_date, "leave_type": l.leave_type.value, "status": l.status.value, "reason": l.reason, "total_days": (l.end_date - l.start_date).days + 1} for l in leaves]
    return {"organization_name": current_user.organization.name, "period": f"{report_in.start_date.strftime('%d/%m/%Y')} - {report_in.end_date.strftime('%d/%m/%Y')}", "data": report_data}

@router.post("/organization/leaves/preview", response_model=schemas.DepartmentLeavesResponse, summary="R7 - Preview Organization Leaves Analysis", tags=["Reports - Organization"], dependencies=[Depends(require_role("admin"))])
def preview_organization_leaves_report(*, db: Session = Depends(get_db), report_in: schemas.OrganizationLeavesRequest, current_user: models.User = Depends(get_current_active_user)):
    if not current_user.organization_id: raise HTTPException(status_code=403, detail="User not associated with an organization.")
    return _get_r7_data(db, report_in, current_user)

@router.post("/organization/leaves/download", summary="R7 - Download Organization Leaves Analysis", tags=["Reports - Organization"], dependencies=[Depends(require_role("admin"))])
async def download_organization_leaves_report(*, db: Session = Depends(get_db), report_in: schemas.OrganizationLeavesRequest, current_user: models.User = Depends(get_current_active_user)):
    if not current_user.organization_id: raise HTTPException(status_code=403, detail="User not associated with an organization.")
    response_data = _get_r7_data(db, report_in, current_user)
    if not response_data["data"]: raise HTTPException(status_code=404, detail="No leave data found for the selected criteria.")
    for row in response_data["data"]: row['department'] = row.get('department_name', 'N/A')
    filename = f"R07_OrgLeaves_{current_user.organization.name}_{report_in.start_date}_to_{report_in.end_date}.{report_in.format.value}"
    context = {"report_title": "Analyse des Absences et Congés", **response_data}
    if report_in.format == schemas.ReportFormat.PDF: return await reporting_service.generate_pdf_from_html("reports/r07_organization_leaves.html", context, filename)
    elif report_in.format in [schemas.ReportFormat.EXCEL, schemas.ReportFormat.CSV]: return await reporting_service.generate_excel(response_data["data"], filename) if report_in.format == schemas.ReportFormat.EXCEL else await reporting_service.generate_csv(response_data["data"], filename)
    else: raise HTTPException(status_code=400, detail="Unsupported format.")


# R2
def _get_r2_data(db: Session, report_in: schemas.ComparativeAnalysisRequest) -> Dict[str, Any]:
    # Simplified period string generation for R2
    if report_in.month:
        period_str = f"{calendar.month_name[report_in.month]} {report_in.year}"
    elif report_in.quarter:
        period_str = f"Q{report_in.quarter} {report_in.year}"
    else:
        period_str = f"Année {report_in.year}"

    report_data = crud.report.get_comparative_analysis_data(db, year=report_in.year, organization_ids=report_in.organization_ids, month=report_in.month, quarter=report_in.quarter)
    if not report_data:
        raise HTTPException(status_code=404, detail="No data found for the selected criteria.")
    return {"period": period_str, "data": report_data}

@router.post("/superuser/comparative-analysis/preview", response_model=schemas.ComparativeAnalysisResponse, summary="R2 - Preview Comparative Analysis Report", tags=["Reports - Super Admin"], dependencies=[Depends(get_current_active_superuser)])
def preview_comparative_analysis_report(*, db: Session = Depends(get_db), report_in: schemas.ComparativeAnalysisRequest):
    return _get_r2_data(db, report_in)

@router.post("/superuser/comparative-analysis/download", summary="R2 - Download Comparative Analysis Report", tags=["Reports - Super Admin"], dependencies=[Depends(get_current_active_superuser)])
async def download_comparative_analysis_report(*, db: Session = Depends(get_db), report_in: schemas.ComparativeAnalysisRequest):
    response_data = _get_r2_data(db, report_in)
    filename = f"R02_ComparativeAnalysis_{response_data['period']}.{report_in.format.value}"
    context = {"report_title": "Analyse Comparative Inter-Organisations", **response_data}
    if report_in.format == schemas.ReportFormat.PDF:
        return await reporting_service.generate_pdf_from_html("reports/r02_comparative_analysis.html", context, filename)
    elif report_in.format == schemas.ReportFormat.EXCEL:
        return await reporting_service.generate_excel(response_data["data"], filename)
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Please choose PDF or Excel.")

# R3
def _get_r3_data(db: Session, report_in: schemas.DeviceUsageRequest) -> Dict[str, Any]:
    report_data = crud.report.get_device_usage_data(db, start_date=report_in.start_date, end_date=report_in.end_date, organization_ids=report_in.organization_ids, site_ids=report_in.site_ids, status=report_in.status)
    if not report_data:
        raise HTTPException(status_code=404, detail="No device data found for the selected criteria.")
    return {"period": f"{report_in.start_date.strftime('%d/%m/%Y')} - {report_in.end_date.strftime('%d/%m/%Y')}", "data": report_data}

@router.post("/superuser/device-usage/preview", response_model=schemas.DeviceUsageResponse, summary="R3 - Preview Device Usage Report", tags=["Reports - Super Admin"], dependencies=[Depends(get_current_active_superuser)])
def preview_device_usage_report(*, db: Session = Depends(get_db), report_in: schemas.DeviceUsageRequest):
    return _get_r3_data(db, report_in)

@router.post("/superuser/device-usage/download", summary="R3 - Download Device Usage Report", tags=["Reports - Super Admin"], dependencies=[Depends(get_current_active_superuser)])
async def download_device_usage_report(*, db: Session = Depends(get_db), report_in: schemas.DeviceUsageRequest):
    response_data = _get_r3_data(db, report_in)
    filename = f"R03_DeviceUsage_{report_in.start_date}_to_{report_in.end_date}.{report_in.format.value}"
    context = {"report_title": "Rapport d'Utilisation des Appareils", **response_data}
    if report_in.format == schemas.ReportFormat.PDF:
        return await reporting_service.generate_pdf_from_html("reports/r03_device_usage.html", context, filename)
    elif report_in.format in [schemas.ReportFormat.EXCEL, schemas.ReportFormat.CSV]:
        return await reporting_service.generate_excel(response_data["data"], filename) if report_in.format == schemas.ReportFormat.EXCEL else await reporting_service.generate_csv(response_data["data"], filename)
    else:
        raise HTTPException(status_code=400, detail="Unsupported format.")

# R4
def _get_r4_data(db: Session, report_in: schemas.UserAuditRequest) -> Dict[str, Any]:
    report_data = crud.report.get_user_audit_data(db, organization_ids=report_in.organization_ids, role_ids=report_in.role_ids, is_active=report_in.is_active)
    if not report_data:
        raise HTTPException(status_code=404, detail="No user data found for the selected criteria.")
    filters = {
        "organizations": report_in.organization_ids,
        "roles": report_in.role_ids,
        "is_active": report_in.is_active
    }
    return {"filters": filters, "user_count": len(report_data), "data": report_data}

@router.post("/superuser/user-audit/preview", response_model=schemas.UserAuditResponse, summary="R4 - Preview User and Role Audit Report", tags=["Reports - Super Admin"], dependencies=[Depends(get_current_active_superuser)])
def preview_user_audit_report(*, db: Session = Depends(get_db), report_in: schemas.UserAuditRequest):
    return _get_r4_data(db, report_in)

@router.post("/superuser/user-audit/download", summary="R4 - Download User and Role Audit Report", tags=["Reports - Super Admin"], dependencies=[Depends(get_current_active_superuser)])
async def download_user_audit_report(*, db: Session = Depends(get_db), report_in: schemas.UserAuditRequest):
    response_data = _get_r4_data(db, report_in)
    filename = f"R04_UserAudit.{report_in.format.value}"
    context = {"report_title": "Audit des Utilisateurs et Rôles", **response_data}
    if report_in.format == schemas.ReportFormat.PDF:
        return await reporting_service.generate_pdf_from_html("reports/r04_user_audit.html", context, filename)
    elif report_in.format == schemas.ReportFormat.EXCEL:
        return await reporting_service.generate_excel(response_data["data"], filename)
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Please choose PDF or Excel.")

# R9
def _get_r9_data(db: Session, report_in: schemas.WorkedHoursRequest, current_user: models.User) -> Dict[str, Any]:
    detailed_data = crud.report.get_organization_worked_hours_data(db, organization_id=current_user.organization_id, start_date=report_in.start_date, end_date=report_in.end_date, department_ids=report_in.department_ids, employee_ids=report_in.employee_ids)
    if not detailed_data: raise HTTPException(status_code=404, detail="No data to generate report.")
    return {"organization_name": current_user.organization.name, "period": f"{report_in.start_date.strftime('%d/%m/%Y')} - {report_in.end_date.strftime('%d/%m/%Y')}", "data": detailed_data}

@router.post("/organization/worked-hours/preview", response_model=schemas.WorkedHoursResponse, summary="R9 - Preview Worked Hours per Employee", tags=["Reports - Organization"], dependencies=[Depends(require_role("admin"))])
def preview_worked_hours_report(*, db: Session = Depends(get_db), report_in: schemas.WorkedHoursRequest, current_user: models.User = Depends(get_current_active_user)):
    if not current_user.organization_id: raise HTTPException(status_code=403, detail="User not associated with an organization.")
    return _get_r9_data(db, report_in, current_user)

@router.post("/organization/worked-hours/download", summary="R9 - Download Worked Hours per Employee", tags=["Reports - Organization"], dependencies=[Depends(require_role("admin"))])
async def download_worked_hours_report(*, db: Session = Depends(get_db), report_in: schemas.WorkedHoursRequest, current_user: models.User = Depends(get_current_active_user)):
    if not current_user.organization_id: raise HTTPException(status_code=403, detail="User not associated with an organization.")
    response_data = _get_r9_data(db, report_in, current_user)
    filename = f"R09_WorkedHours_{current_user.organization.name}_{report_in.start_date}_to_{report_in.end_date}.{report_in.format.value}"
    context = {"report_title": "Rapport des Heures Travaillées", **response_data}
    if report_in.format == schemas.ReportFormat.PDF: return await reporting_service.generate_pdf_from_html("reports/r09_worked_hours.html", context, filename)
    elif report_in.format in [schemas.ReportFormat.EXCEL, schemas.ReportFormat.CSV]:
        for row in response_data["data"]: row["date"] = row["date"].isoformat()
        return await reporting_service.generate_excel(response_data["data"], filename) if report_in.format == schemas.ReportFormat.EXCEL else await reporting_service.generate_csv(response_data["data"], filename)
    else: raise HTTPException(status_code=400, detail="Unsupported format.")

# R10
def _get_r10_data(db: Session, report_in: schemas.SiteActivityRequest, current_user: models.User) -> Dict[str, Any]:
    report_data = crud.report.get_site_activity_data(db, organization_id=current_user.organization_id, start_date=report_in.start_date, end_date=report_in.end_date, site_ids=report_in.site_ids)
    if not report_data: raise HTTPException(status_code=404, detail="Could not generate report for the selected sites.")
    return {"organization_name": current_user.organization.name, "period": f"{report_in.start_date.strftime('%d/%m/%Y')} - {report_in.end_date.strftime('%d/%m/%Y')}", "data": report_data}

@router.post("/organization/site-activity/preview", response_model=schemas.SiteActivityResponse, summary="R10 - Preview Site Activity Report", tags=["Reports - Organization"], dependencies=[Depends(require_role("admin"))])
def preview_site_activity_report(*, db: Session = Depends(get_db), report_in: schemas.SiteActivityRequest, current_user: models.User = Depends(get_current_active_user)):
    if not current_user.organization_id: raise HTTPException(status_code=403, detail="User not associated with an organization.")
    return _get_r10_data(db, report_in, current_user)

@router.post("/organization/site-activity/download", summary="R10 - Download Site Activity Report", tags=["Reports - Organization"], dependencies=[Depends(require_role("admin"))])
async def download_site_activity_report(*, db: Session = Depends(get_db), report_in: schemas.SiteActivityRequest, current_user: models.User = Depends(get_current_active_user)):
    if not current_user.organization_id: raise HTTPException(status_code=403, detail="User not associated with an organization.")
    response_data = _get_r10_data(db, report_in, current_user)
    filename = f"R10_SiteActivity_{current_user.organization.name}_{report_in.start_date}_to_{report_in.end_date}.{report_in.format.value}"
    context = {"report_title": "Rapport d'Activité par Site", **response_data}
    if report_in.format == schemas.ReportFormat.PDF: return await reporting_service.generate_pdf_from_html("reports/r10_site_activity.html", context, filename)
    elif report_in.format == schemas.ReportFormat.EXCEL: return await reporting_service.generate_excel(response_data["data"], filename)
    else: raise HTTPException(status_code=400, detail="Unsupported format. Please choose PDF or Excel.")

#
# Reports for Super Admins (R1-R4)
#

# R1
def _get_r1_data(db: Session, report_in: schemas.MultiOrgConsolidatedRequest) -> Dict[str, Any]:
    if report_in.metric_type not in ["presence", "leaves"]: raise HTTPException(status_code=400, detail="Invalid metric_type. Choose 'presence' or 'leaves'.")
    report_data = crud.report.get_multi_org_consolidated_data(db, start_date=report_in.start_date, end_date=report_in.end_date, organization_ids=report_in.organization_ids)
    if not report_data: raise HTTPException(status_code=404, detail="No data found for the selected criteria.")
    return {"period": f"{report_in.start_date.strftime('%d/%m/%Y')} - {report_in.end_date.strftime('%d/%m/%Y')}", "data": report_data}

@router.post("/superuser/multi-org-consolidated/preview", response_model=schemas.MultiOrgConsolidatedResponse, summary="R1 - Preview Multi-Org Consolidated Report", tags=["Reports - Super Admin"], dependencies=[Depends(get_current_active_superuser)])
def preview_multi_org_consolidated_report(*, db: Session = Depends(get_db), report_in: schemas.MultiOrgConsolidatedRequest):
    return _get_r1_data(db, report_in)

@router.post("/superuser/multi-org-consolidated/download", summary="R1 - Download Multi-Org Consolidated Report", tags=["Reports - Super Admin"], dependencies=[Depends(get_current_active_superuser)])
async def download_multi_org_consolidated_report(*, db: Session = Depends(get_db), report_in: schemas.MultiOrgConsolidatedRequest):
    response_data = _get_r1_data(db, report_in)
    period_str = f"{report_in.start_date.strftime('%Y%m%d')}-{report_in.end_date.strftime('%Y%m%d')}"
    filename = f"R01_MultiOrg_{report_in.metric_type}_{period_str}.{report_in.format.value}"
    context = {"report_title": "Rapport Consolidé Multi-Organisations", **response_data}
    if report_in.format == schemas.ReportFormat.PDF: return await reporting_service.generate_pdf_from_html("reports/r01_multi_org_consolidated.html", context, filename)
    elif report_in.format in [schemas.ReportFormat.EXCEL, schemas.ReportFormat.CSV]: return await reporting_service.generate_excel(response_data["data"], filename) if report_in.format == schemas.ReportFormat.EXCEL else await reporting_service.generate_csv(response_data["data"], filename)
    else: raise HTTPException(status_code=400, detail="Unsupported format.")