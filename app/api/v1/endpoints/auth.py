from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.crud.attendance import attendance as attendance_crud
from app.crud.employee import employee as employee_crud
from app.schemas.attendance import (
    Attendance, 
    AttendanceCreate, 
    AttendanceUpdate,
    AttendanceList,
    DailyStats
)
from app.models.user import User, UserRole
from app.models.attendance import AttendanceStatus
from app.dependencies import get_current_active_user, require_role

router = APIRouter()


@router.post("/", response_model=Attendance, status_code=status.HTTP_201_CREATED)
def create_attendance(
    *,
    db: Session = Depends(get_db),
    attendance_in: AttendanceCreate,
    current_user: User = Depends(get_current_active_user),
) -> Attendance:
    """
    Créer un pointage
    """
    # Vérifier que l'employé existe
    employee = employee_crud.get(db, id=attendance_in.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employé non trouvé"
        )
    
    # Créer le pointage
    attendance = attendance_crud.create(db, obj_in=attendance_in)
    return attendance


@router.get("/", response_model=AttendanceList)
def read_attendances(
    db: Session = Depends(get_db),
    organization_id: int = Query(..., description="ID de l'organisation"),
    employee_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
) -> AttendanceList:
    """
    Récupérer les pointages avec filtres
    """
    if start_date and end_date:
        attendances = attendance_crud.get_by_date_range(
            db,
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date,
            employee_id=employee_id
        )
    elif employee_id:
        attendances = attendance_crud.get_by_employee(
            db,
            employee_id=employee_id,
            skip=skip,
            limit=limit
        )
    else:
        attendances = attendance_crud.get_multi(db, skip=skip, limit=limit)
    
    total = len(attendances)
    
    return {
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit,
        "attendances": attendances[skip:skip+limit]
    }


@router.get("/today", response_model=List[Attendance])
def read_today_attendances(
    db: Session = Depends(get_db),
    organization_id: int = Query(..., description="ID de l'organisation"),
    current_user: User = Depends(get_current_active_user),
) -> List[Attendance]:
    """
    Récupérer tous les pointages du jour
    """
    attendances = attendance_crud.get_today_attendances(
        db,
        organization_id=organization_id
    )
    return attendances


@router.get("/stats/daily", response_model=DailyStats)
def get_daily_stats(
    db: Session = Depends(get_db),
    organization_id: int = Query(..., description="ID de l'organisation"),
    target_date: Optional[date] = None,
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.ADMIN)),
) -> DailyStats:
    """
    Récupérer les statistiques quotidiennes de présence
    """
    if target_date is None:
        target_date = date.today()
    
    # Compter par statut
    present = attendance_crud.count_by_status(
        db,
        organization_id=organization_id,
        status=AttendanceStatus.PRESENT,
        target_date=target_date
    )
    
    absent = attendance_crud.count_by_status(
        db,
        organization_id=organization_id,
        status=AttendanceStatus.ABSENT,
        target_date=target_date
    )
    
    late = attendance_crud.count_by_status(
        db,
        organization_id=organization_id,
        status=AttendanceStatus.LATE,
        target_date=target_date
    )
    
    on_leave = attendance_crud.count_by_status(
        db,
        organization_id=organization_id,
        status=AttendanceStatus.ON_LEAVE,
        target_date=target_date
    )
    
    # Total des employés
    total_employees = employee_crud.count_by_organization(
        db,
        organization_id=organization_id
    )
    
    # Calculer le taux de présence
    attendance_rate = (present / total_employees * 100) if total_employees > 0 else 0
    
    return {
        "date": target_date.isoformat(),
        "total_employees": total_employees,
        "present": present,
        "absent": absent,
        "late": late,
        "on_leave": on_leave,
        "attendance_rate": round(attendance_rate, 2)
    }


@router.get("/employee/{employee_id}", response_model=List[Attendance])
def read_employee_attendances(
    employee_id: UUID,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
) -> List[Attendance]:
    """
    Récupérer l'historique des pointages d'un employé
    """
    # Vérifier que l'employé existe
    employee = employee_crud.get(db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employé non trouvé"
        )
    
    attendances = attendance_crud.get_by_employee(
        db,
        employee_id=employee_id,
        skip=skip,
        limit=limit
    )
    return attendances


@router.put("/{attendance_id}", response_model=Attendance)
def update_attendance(
    *,
    db: Session = Depends(get_db),
    attendance_id: int,
    attendance_in: AttendanceUpdate,
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.ADMIN)),
) -> Attendance:
    """
    Mettre à jour un pointage (correction)
    """
    attendance = attendance_crud.get(db, id=attendance_id)
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pointage non trouvé"
        )
    
    attendance = attendance_crud.update(db, db_obj=attendance, obj_in=attendance_in)
    return attendance


@router.delete("/{attendance_id}", response_model=Attendance)
def delete_attendance(
    *,
    db: Session = Depends(get_db),
    attendance_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> Attendance:
    """
    Supprimer un pointage
    """
    attendance = attendance_crud.get(db, id=attendance_id)
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pointage non trouvé"
        )
    
    attendance = attendance_crud.delete(db, id=attendance_id)
    return attendance