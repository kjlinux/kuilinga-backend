from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import date, timedelta
import io
from app.db.session import get_db
from app.schemas.report import (
    ReportRequest,
    AttendanceReport,
    ReportFormat,
    ReportPeriod
)
from app.services.report_service import report_service
from app.models.user import User, UserRole
from app.dependencies import require_role

router = APIRouter()


@router.post("/attendance", response_model=AttendanceReport)
def generate_attendance_report(
    *,
    db: Session = Depends(get_db),
    report_request: ReportRequest,
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.ADMIN)),
) -> AttendanceReport:
    """
    Générer un rapport de présence (format JSON)
    """
    report = report_service.generate_attendance_report(
        db=db,
        organization_id=report_request.organization_id,
        start_date=report_request.start_date,
        end_date=report_request.end_date,
        employee_ids=report_request.employee_ids,
        department=report_request.department
    )
    
    return report


@router.post("/attendance/export")
def export_attendance_report(
    *,
    db: Session = Depends(get_db),
    report_request: ReportRequest,
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.ADMIN)),
):
    """
    Exporter un rapport de présence (PDF, Excel, CSV)
    """
    # Générer le rapport
    report = report_service.generate_attendance_report(
        db=db,
        organization_id=report_request.organization_id,
        start_date=report_request.start_date,
        end_date=report_request.end_date,
        employee_ids=report_request.employee_ids,
        department=report_request.department
    )
    
    # Exporter selon le format demandé
    if report_request.format == ReportFormat.CSV:
        content = report_service.export_to_csv(report)
        media_type = "text/csv"
        filename = f"rapport_presence_{report_request.start_date}_{report_request.end_date}.csv"
        return StreamingResponse(
            io.StringIO(content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    elif report_request.format == ReportFormat.EXCEL:
        content = report_service.export_to_excel(report)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"rapport_presence_{report_request.start_date}_{report_request.end_date}.xlsx"
        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    elif report_request.format == ReportFormat.PDF:
        content = report_service.export_to_pdf(report)
        media_type = "application/pdf"
        filename = f"rapport_presence_{report_request.start_date}_{report_request.end_date}.pdf"
        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Format de rapport non supporté"
    )


@router.get("/attendance/daily")
def get_daily_report(
    *,
    db: Session = Depends(get_db),
    organization_id: int = Query(..., description="ID de l'organisation"),
    target_date: date = Query(default=None, description="Date cible (par défaut aujourd'hui)"),
    format: ReportFormat = Query(ReportFormat.PDF, description="Format d'export"),
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.ADMIN)),
):
    """
    Générer un rapport quotidien
    """
    if target_date is None:
        target_date = date.today()
    
    report_request = ReportRequest(
        organization_id=organization_id,
        period=ReportPeriod.DAILY,
        start_date=target_date,
        end_date=target_date,
        format=format
    )
    
    return export_attendance_report(
        db=db,
        report_request=report_request,
        current_user=current_user
    )


@router.get("/attendance/weekly")
def get_weekly_report(
    *,
    db: Session = Depends(get_db),
    organization_id: int = Query(..., description="ID de l'organisation"),
    week_start: date = Query(default=None, description="Début de semaine (par défaut cette semaine)"),
    format: ReportFormat = Query(ReportFormat.PDF, description="Format d'export"),
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.ADMIN)),
):
    """
    Générer un rapport hebdomadaire
    """
    if week_start is None:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
    
    week_end = week_start + timedelta(days=6)
    
    report_request = ReportRequest(
        organization_id=organization_id,
        period=ReportPeriod.WEEKLY,
        start_date=week_start,
        end_date=week_end,
        format=format
    )
    
    return export_attendance_report(
        db=db,
        report_request=report_request,
        current_user=current_user
    )


@router.get("/attendance/monthly")
def get_monthly_report(
    *,
    db: Session = Depends(get_db),
    organization_id: int = Query(..., description="ID de l'organisation"),
    year: int = Query(..., description="Année"),
    month: int = Query(..., ge=1, le=12, description="Mois (1-12)"),
    format: ReportFormat = Query(ReportFormat.PDF, description="Format d'export"),
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.ADMIN)),
):
    """
    Générer un rapport mensuel
    """
    # Premier jour du mois
    start_date = date(year, month, 1)
    
    # Dernier jour du mois
    if month == 12:
        end_date = date(year, 12, 31)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    report_request = ReportRequest(
        organization_id=organization_id,
        period=ReportPeriod.MONTHLY,
        start_date=start_date,
        end_date=end_date,
        format=format
    )
    
    return export_attendance_report(
        db=db,
        report_request=report_request,
        current_user=current_user
    )


@router.get("/attendance/employee/{employee_id}")
def get_employee_report(
    *,
    db: Session = Depends(get_db),
    employee_id: int,
    organization_id: int = Query(..., description="ID de l'organisation"),
    start_date: date = Query(..., description="Date de début"),
    end_date: date = Query(..., description="Date de fin"),
    format: ReportFormat = Query(ReportFormat.PDF, description="Format d'export"),
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.ADMIN)),
):
    """
    Générer un rapport pour un employé spécifique
    """
    report_request = ReportRequest(
        organization_id=organization_id,
        period=ReportPeriod.CUSTOM,
        start_date=start_date,
        end_date=end_date,
        format=format,
        employee_ids=[employee_id]
    )
    
    return export_attendance_report(
        db=db,
        report_request=report_request,
        current_user=current_user
    )