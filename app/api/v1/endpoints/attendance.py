from typing import List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app import dependencies

router = APIRouter()

@router.get("/", response_model=List[schemas.Attendance])
def read_attendances(
    employee_id: UUID,
    db: Session = Depends(dependencies.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(dependencies.get_current_active_user),
) -> Any:
    """
    Récupérer les pointages d'un employé.
    """
    employee = crud.employee.get(db, id=employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    if not crud.user.is_superuser(current_user):
        if not current_user.employee or current_user.employee.organization_id != employee.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    attendances = crud.attendance.get_multi_by_employee(
        db, employee_id=employee_id, skip=skip, limit=limit
    )
    return attendances

@router.post("/", response_model=schemas.Attendance, status_code=status.HTTP_201_CREATED)
def create_attendance(
    *,
    db: Session = Depends(dependencies.get_db),
    attendance_in: schemas.AttendanceCreate,
    # This endpoint might be called by a device or a user
    # For now, we'll allow any authenticated user to create an attendance record
    # but we should add more granular permissions later.
    current_user: models.User = Depends(dependencies.get_current_active_user),
) -> Any:
    """
    Créer un nouveau pointage.
    """
    employee = crud.employee.get(db, id=attendance_in.employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if not crud.user.is_superuser(current_user):
        # A user can create attendance for themselves
        if current_user.id == employee.user_id:
            pass
        # A manager can create attendance for anyone in their organization
        elif current_user.role == models.user.UserRole.MANAGER and current_user.employee and current_user.employee.organization_id == employee.organization_id:
            pass
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to create attendance for this employee")

    attendance = crud.attendance.create(db=db, obj_in=attendance_in)
    return attendance