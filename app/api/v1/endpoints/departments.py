from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.dependencies import get_db, PermissionChecker

router = APIRouter()

@router.post(
    "/",
    response_model=schemas.Department,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker(["department:create"]))],
)
def create_department(
    *,
    db: Session = Depends(get_db),
    department_in: schemas.DepartmentCreate,
):
    """
    Create a new department. Requires permission: `department:create`.
    """
    department = crud.department.create(db=db, obj_in=department_in)
    return department

@router.get(
    "/",
    response_model=schemas.PaginatedResponse[schemas.Department],
    dependencies=[Depends(PermissionChecker(["department:read"]))],
)
def read_departments(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Nombre de départements à sauter"),
    limit: int = Query(100, description="Nombre maximum de départements à retourner"),
) -> Any:
    """
    Retrieve departments. Requires permission: `department:read`.
    """
    department_data = crud.department.get_multi(db, skip=skip, limit=limit)
    return {
        "items": department_data["items"],
        "total": department_data["total"],
        "skip": skip,
        "limit": limit,
    }

@router.get(
    "/{department_id}",
    response_model=schemas.Department,
    dependencies=[Depends(PermissionChecker(["department:read"]))],
)
def read_department(
    *,
    db: Session = Depends(get_db),
    department_id: str,
):
    """
    Get department by ID. Requires permission: `department:read`.
    """
    department = crud.department.get(db=db, id=department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department

@router.put(
    "/{department_id}",
    response_model=schemas.Department,
    dependencies=[Depends(PermissionChecker(["department:update"]))],
)
def update_department(
    *,
    db: Session = Depends(get_db),
    department_id: str,
    department_in: schemas.DepartmentUpdate,
):
    """
    Update a department. Requires permission: `department:update`.
    """
    department = crud.department.get(db=db, id=department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    department = crud.department.update(db=db, db_obj=department, obj_in=department_in)
    return department

@router.delete(
    "/{department_id}",
    response_model=schemas.Department,
    dependencies=[Depends(PermissionChecker(["department:delete"]))],
)
def delete_department(
    *,
    db: Session = Depends(get_db),
    department_id: str,
):
    """
    Delete a department. Requires permission: `department:delete`.
    """
    department = crud.department.get(db=db, id=department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    department = crud.department.remove(db=db, id=department_id)
    return department
