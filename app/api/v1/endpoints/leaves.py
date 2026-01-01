from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Any
from app import crud, models, schemas
from app.dependencies import get_db, PermissionChecker, get_current_active_user

router = APIRouter()

@router.post(
    "/",
    response_model=schemas.Leave,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker(["leave:create"]))],
)
def create_leave(
    *,
    db: Session = Depends(get_db),
    leave_in: schemas.LeaveCreate,
    current_user: models.User = Depends(get_current_active_user),
):
    employee = crud.employee.get(db=db, id=leave_in.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not current_user.is_superuser and employee.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to create leave for this employee")

    leave = crud.leave.create(db=db, obj_in=leave_in)
    db.refresh(leave, ["employee.department", "approver"])
    return leave

@router.get(
    "/",
    response_model=schemas.PaginatedResponse[schemas.Leave],
    dependencies=[Depends(PermissionChecker(["leave:read"]))],
)
def read_leaves(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Nombre de demandes de congé à sauter"),
    limit: int = Query(100, description="Nombre maximum de demandes de congé à retourner"),
    search: str = Query(None, description="Recherche textuelle (type de congé, statut, raison)"),
    sort_by: str = Query(None, description="Champ de tri (leave_type, status, start_date, end_date, created_at, updated_at)"),
    sort_order: str = Query("asc", description="Direction du tri (asc ou desc)"),
) -> Any:
    leave_data = crud.leave.get_multi_paginated(
        db,
        skip=skip,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return {
        "items": leave_data["items"],
        "total": leave_data["total"],
        "skip": skip,
        "limit": limit,
    }

@router.get(
    "/{leave_id}",
    response_model=schemas.Leave,
    dependencies=[Depends(PermissionChecker(["leave:read"]))],
)
def read_leave(
    *,
    db: Session = Depends(get_db),
    leave_id: str,
):
    leave = crud.leave.get(db=db, id=leave_id)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return leave

@router.put(
    "/{leave_id}",
    response_model=schemas.Leave,
    dependencies=[Depends(PermissionChecker(["leave:update"]))],
)
def update_leave(
    *,
    db: Session = Depends(get_db),
    leave_id: str,
    leave_in: schemas.LeaveUpdate,
    current_user: models.User = Depends(get_current_active_user),
):
    leave = crud.leave.get(db=db, id=leave_id)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    # The original update logic is preserved but we add the approver_id
    updated_leave_data = leave_in.dict(exclude_unset=True)
    if updated_leave_data.get("status"):
        # Set the current user as the approver
        updated_leave_data["approver_id"] = current_user.id

    leave = crud.leave.update(db=db, db_obj=leave, obj_in=updated_leave_data)
    db.refresh(leave, ["employee.department", "approver"])
    return leave

@router.delete(
    "/{leave_id}",
    response_model=schemas.Leave,
    dependencies=[Depends(PermissionChecker(["leave:delete"]))],
)
def delete_leave(
    *,
    db: Session = Depends(get_db),
    leave_id: str,
):
    leave = crud.leave.get(db=db, id=leave_id)
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    # We need to load relations before deleting to return them
    db.refresh(leave, ["employee.department", "approver"])
    crud.leave.remove(db=db, id=leave_id)
    return leave