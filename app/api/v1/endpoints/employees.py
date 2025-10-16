from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.dependencies import get_db, PermissionChecker

router = APIRouter()

@router.get(
    "/",
    response_model=schemas.PaginatedResponse[schemas.Employee],
    summary="Lister les employés",
    description="Récupère une liste d'employés avec les détails du département, du site et de l'organisation. Requiert la permission `employee:read`.",
    dependencies=[Depends(PermissionChecker(["employee:read"]))],
)
def read_employees(
    db: Session = Depends(get_db),
    organization_id: str = Query(None, description="Filtrer par ID d'organisation"),
    skip: int = Query(0, description="Nombre d'employés à sauter"),
    limit: int = Query(100, description="Nombre maximum d'employés à retourner"),
) -> Any:
    """
    Retrieve employees with enriched data.
    """
    employee_data = crud.employee.get_multi_paginated(
        db, skip=skip, limit=limit, organization_id=organization_id
    )

    return {
        "items": employee_data["items"],
        "total": employee_data["total"],
        "skip": skip,
        "limit": limit,
    }

@router.post(
    "/",
    response_model=schemas.Employee,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouvel employé",
    description="Crée un nouvel employé. Requiert la permission `employee:create`.",
    dependencies=[Depends(PermissionChecker(["employee:create"]))],
)
def create_employee(
    *,
    db: Session = Depends(get_db),
    employee_in: schemas.EmployeeCreate,
) -> Any:
    """
    Create new employee.
    """
    # Vérifier si l'organisation existe
    organization = crud.organization.get(db, id=employee_in.organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"L'organisation avec l'ID {employee_in.organization_id} n'a pas été trouvée.",
        )

    employee = crud.employee.create(db=db, obj_in=employee_in)

    # Re-fetch with relationships for the response
    db.refresh(employee)
    enriched_employee = crud.employee.get(db, id=employee.id)

    return enriched_employee