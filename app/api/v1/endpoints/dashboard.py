from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import crud, schemas
from app.dependencies import get_db

router = APIRouter()

@router.get("/admin", response_model=schemas.dashboard.AdminDashboard)
def get_admin_dashboard_data(db: Session = Depends(get_db)):
    """
    Retrieve System Administrator dashboard data.
    """
    active_organizations = crud.dashboard.get_active_organizations_count(db=db)
    users_per_organization = crud.dashboard.get_users_per_organization(db=db)
    sites_per_organization = crud.dashboard.get_sites_per_organization(db=db)
    device_status_ratio = crud.dashboard.get_device_status_ratio(db=db)
    daily_attendance_count = crud.dashboard.get_daily_attendance_count(db=db)
    plan_distribution = crud.dashboard.get_plan_distribution(db=db)
    top_10_organizations_by_employees = crud.dashboard.get_top_10_organizations_by_employees(db=db)

    return {
        "active_organizations": active_organizations,
        "users_per_organization": users_per_organization,
        "sites_per_organization": sites_per_organization,
        "device_status_ratio": device_status_ratio,
        "daily_attendance_count": daily_attendance_count,
        "plan_distribution": plan_distribution,
        "top_10_organizations_by_employees": top_10_organizations_by_employees,
    }


@router.get("/manager/{organization_id}", response_model=schemas.dashboard.ManagerDashboard)
def get_manager_dashboard_data(organization_id: str, db: Session = Depends(get_db)):
    """
    Retrieve Manager/HR dashboard data for a specific organization.
    """
    present_today, total_employees = crud.dashboard.get_daily_presence_and_total_employees(db=db, organization_id=organization_id)
    absent_today = total_employees - present_today
    tardy_today = crud.dashboard.get_daily_tardiness_count(db=db, organization_id=organization_id)
    attendance_rate = crud.dashboard.get_attendance_rate(db=db, organization_id=organization_id)
    total_work_hours = crud.dashboard.get_total_work_hours(db=db, organization_id=organization_id)
    pending_leaves = crud.dashboard.get_pending_leaves_count(db=db, organization_id=organization_id)
    presence_evolution = crud.dashboard.get_presence_evolution_last_30_days(db=db, organization_id=organization_id)
    presence_absence_tardiness_distribution = crud.dashboard.get_presence_absence_tardiness_distribution(db=db, organization_id=organization_id)
    real_time_attendances = crud.dashboard.get_real_time_attendances(db=db, organization_id=organization_id)

    return {
        "present_today": present_today,
        "absent_today": absent_today,
        "tardy_today": tardy_today,
        "attendance_rate": attendance_rate,
        "total_work_hours": total_work_hours,
        "pending_leaves": pending_leaves,
        "presence_evolution": presence_evolution,
        "presence_absence_tardiness_distribution": presence_absence_tardiness_distribution,
        "real_time_attendances": real_time_attendances,
    }


@router.get("/employee/{employee_id}", response_model=schemas.dashboard.EmployeeDashboard)
def get_employee_dashboard_data(employee_id: str, db: Session = Depends(get_db)):
    """
    Retrieve Employee dashboard data for a specific employee.
    """
    today_attendances = crud.dashboard.get_employee_today_attendances(db=db, employee_id=employee_id)
    monthly_attendance_rate = crud.dashboard.get_employee_monthly_attendance_rate(db=db, employee_id=employee_id)
    leave_balance = crud.dashboard.get_employee_leave_balance(db=db, employee_id=employee_id)

    return {
        "today_attendances": today_attendances,
        "monthly_attendance_rate": monthly_attendance_rate,
        "leave_balance": leave_balance,
    }


@router.get("/integrator/{organization_id}", response_model=schemas.dashboard.IntegratorDashboard)
def get_integrator_dashboard_data(organization_id: str, db: Session = Depends(get_db)):
    """
    Retrieve Integrator/IoT Technician dashboard data for a specific organization.
    """
    device_status_ratio = crud.dashboard.get_device_status_ratio(db=db)
    attendance_per_device = crud.dashboard.get_attendance_per_device(db=db, organization_id=organization_id)

    return {
        "device_status_ratio": device_status_ratio,
        "attendance_per_device": attendance_per_device,
    }


@router.get("/analytics/{organization_id}", response_model=schemas.dashboard.AdvancedAnalytics)
def get_advanced_analytics_data(organization_id: str, db: Session = Depends(get_db)):
    """
    Retrieve Advanced Analytics data for a specific organization.
    """
    tardiness_by_day_of_week = crud.dashboard.get_tardiness_by_day_of_week(db=db, organization_id=organization_id)

    return {
        "tardiness_by_day_of_week": tardiness_by_day_of_week,
    }