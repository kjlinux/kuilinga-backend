from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.dependencies import get_db, get_current_active_user

router = APIRouter()

@router.get(
    "/",
    response_model=List[schemas.Attendance],
    summary="Lister les pointages",
    description=(
        "Récupère une liste de pointages. "
        "Les employés ne peuvent voir que leurs propres pointages. "
        "Les managers peuvent voir tous les pointages de leur organisation. "
        "Les admins peuvent tout voir."
    ),
    responses={
        403: {"description": "Permissions insuffisantes ou ID d'employé requis"},
        404: {"description": "Employé non trouvé"},
    },
)
def read_attendances(
    db: Session = Depends(get_db),
    employee_id: str = Query(None, description="Filtrer par ID d'employé"),
    skip: int = Query(0, description="Nombre de pointages à sauter"),
    limit: int = Query(100, description="Nombre maximum de pointages à retourner"),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    if employee_id:
        employee = crud.employee.get(db, id=employee_id)
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")

        if not current_user.is_superuser:
            if current_user.organization_id != employee.organization_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")
            if current_user.role == models.UserRole.EMPLOYEE and current_user.id != employee.user_id:
                 raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")

        attendances = crud.attendance.get_multi_by_employee(db, employee_id=employee_id, skip=skip, limit=limit)
    else:
        if not current_user.is_superuser:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Un ID d'employé est requis pour les non-administrateurs")
        attendances = crud.attendance.get_multi(db, skip=skip, limit=limit)

    return attendances

@router.post(
    "/",
    response_model=schemas.Attendance,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouveau pointage",
    description=(
        "Enregistre un nouvel événement de pointage (entrée ou sortie). "
        "Peut être appelé par un terminal (via une clé API) ou un utilisateur authentifié."
    ),
    responses={
        403: {"description": "Permissions insuffisantes pour pointer pour cet employé"},
        404: {"description": "Employé non trouvé"},
    },
)
def create_attendance(
    *,
    db: Session = Depends(get_db),
    attendance_in: schemas.AttendanceCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    employee = crud.employee.get(db, id=attendance_in.employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")

    if not current_user.is_superuser:
        if current_user.role == models.UserRole.EMPLOYEE and (not employee.user_id or current_user.id != employee.user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Un employé ne peut pointer que pour lui-même.")
        elif current_user.organization_id != employee.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes pour cette organisation.")

    attendance = crud.attendance.create(db=db, obj_in=attendance_in)
    return attendance