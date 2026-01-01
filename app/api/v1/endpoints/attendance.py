import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app import crud, models, schemas
from app.dependencies import get_db, PermissionChecker, get_current_active_user
from app.models.attendance import AttendanceType
from app.websocket.connection_manager import manager

router = APIRouter()

@router.get(
    "/",
    response_model=schemas.PaginatedResponse[schemas.Attendance],
    summary="Lister les pointages",
    description="Récupère une liste de pointages avec les détails de l'employé, du département, du site et du dispositif. Requiert la permission `attendance:read`.",
    dependencies=[Depends(PermissionChecker(["attendance:read"]))],
)
def read_attendances(
    db: Session = Depends(get_db),
    employee_id: str = Query(None, description="Filtrer par ID d'employé"),
    skip: int = Query(0, description="Nombre de pointages à sauter"),
    limit: int = Query(100, description="Nombre maximum de pointages à retourner"),
    search: str = Query(None, description="Recherche textuelle (type de pointage)"),
    sort_by: str = Query(None, description="Champ de tri (timestamp, type, created_at, updated_at)"),
    sort_order: str = Query("asc", description="Direction du tri (asc ou desc)"),
) -> Any:
    """
    Retrieve attendances with enriched data.
    """
    attendance_data = crud.attendance.get_multi_paginated(
        db,
        skip=skip,
        limit=limit,
        employee_id=employee_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # Note: The duration calculation logic will be added later.
    # For now, the 'duration' field will be None.

    return {
        "items": attendance_data["items"],
        "total": attendance_data["total"],
        "skip": skip,
        "limit": limit,
    }

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

    # Re-fetch the attendance with relationships for the response and broadcast
    db.refresh(attendance)

    # This is not the most efficient way, but it ensures all relationships are loaded for the response.
    # A more optimized approach would be to build the response schema manually.
    enriched_attendance = crud.attendance.get(db, id=attendance.id)

    # Broadcast the new attendance record
    if enriched_attendance:
      attendance_data = schemas.Attendance.from_orm(enriched_attendance).dict()
      message_to_broadcast = {
          "type": "new_attendance",
          "payload": attendance_data
      }
      await manager.broadcast(json.dumps(message_to_broadcast, default=str))

    return enriched_attendance


@router.post(
    "/clock",
    response_model=schemas.Attendance,
    summary="Pointage manuel (Clock-in/Clock-out)",
    description="Permet à un utilisateur authentifié de pointer son arrivée ou son départ. Le système détermine automatiquement s'il s'agit d'une entrée ou d'une sortie.",
)
async def manual_clock(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Handles a manual clock-in or clock-out for the authenticated user.
    """
    if not current_user.employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="L'utilisateur n'est pas associé à un profil employé.",
        )

    employee_id = current_user.employee.id
    last_attendance = crud.attendance.get_last_for_employee(db, employee_id=employee_id)

    new_attendance_type = AttendanceType.IN
    if last_attendance and last_attendance.type == AttendanceType.IN:
        new_attendance_type = AttendanceType.OUT

    attendance_in = schemas.AttendanceCreate(
        timestamp=datetime.utcnow(),
        type=new_attendance_type,
        employee_id=employee_id,
        device_id=None,  # Manual entry has no device
    )

    attendance = crud.attendance.create(db=db, obj_in=attendance_in)
    db.refresh(attendance)

    enriched_attendance = crud.attendance.get(db, id=attendance.id)
    if enriched_attendance:
        attendance_data = schemas.Attendance.from_orm(enriched_attendance).dict()
        message_to_broadcast = {
            "type": "new_attendance",
            "payload": attendance_data
        }
        await manager.broadcast(json.dumps(message_to_broadcast, default=str))

    return enriched_attendance