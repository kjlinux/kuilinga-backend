from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.dependencies import get_db, PermissionChecker

router = APIRouter()

def enrich_department_response(db: Session, dept: models.Department) -> schemas.Department:
    """
    Enrich the department object with site, manager details, and employee count.
    """
    dept_schema = schemas.Department.from_orm(dept)
    dept_schema.employees_count = crud.employee.count_by_department(db, department_id=dept.id)
    return dept_schema

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
    department = crud.department.create(db=db, obj_in=department_in)
    db.refresh(department, ["site", "manager"])
    return enrich_department_response(db, department)

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
    department_data = crud.department.get_multi_paginated(db, skip=skip, limit=limit)
    enriched_items = [enrich_department_response(db, dept) for dept in department_data["items"]]
    return {
        "items": enriched_items,
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
    department = crud.department.get(db=db, id=department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return enrich_department_response(db, department)

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
    department = crud.department.get(db=db, id=department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    department = crud.department.update(db=db, db_obj=department, obj_in=department_in)
    db.refresh(department, ["site", "manager"])
    return enrich_department_response(db, department)

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
    department = crud.department.get(db=db, id=department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    # We enrich before deleting to have the data for the response
    enriched_dept = enrich_department_response(db, department)
    crud.department.remove(db=db, id=department_id)
    return enriched_dept