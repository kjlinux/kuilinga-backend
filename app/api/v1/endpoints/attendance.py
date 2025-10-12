import json
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.dependencies import get_db, PermissionChecker
from app.websocket.connection_manager import manager

router = APIRouter()

@router.get(
    "/",
    response_model=List[schemas.Attendance],
    summary="Lister les pointages",
    description="Récupère une liste de pointages. Requiert la permission `attendance:read`.",
    dependencies=[Depends(PermissionChecker(["attendance:read"]))],
)
def read_attendances(
    db: Session = Depends(get_db),
    employee_id: str = Query(None, description="Filtrer par ID d'employé"),
    skip: int = Query(0, description="Nombre de pointages à sauter"),
    limit: int = Query(100, description="Nombre maximum de pointages à retourner"),
) -> Any:
    if employee_id:
        attendances = crud.attendance.get_multi_by_employee(db, employee_id=employee_id, skip=skip, limit=limit)
    else:
        attendances = crud.attendance.get_multi(db, skip=skip, limit=limit)
    return attendances

@router.post(
    "/",
    response_model=schemas.Attendance,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouveau pointage",
    description="Enregistre un pointage et diffuse l'événement. Requiert la permission `attendance:create`.",
    dependencies=[Depends(PermissionChecker(["attendance:create"]))],
)
async def create_attendance(
    *,
    db: Session = Depends(get_db),
    attendance_in: schemas.AttendanceCreate,
) -> Any:
    employee = crud.employee.get(db, id=attendance_in.employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")

    attendance = crud.attendance.create(db=db, obj_in=attendance_in)

    # Broadcast the new attendance record
    attendance_data = schemas.Attendance.from_orm(attendance).dict()
    message_to_broadcast = {
        "type": "new_attendance",
        "payload": attendance_data
    }
    await manager.broadcast(json.dumps(message_to_broadcast, default=str))

    return attendance
