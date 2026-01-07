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
    search: str = Query(None, description="Recherche textuelle (nom, prénom, email, badge, téléphone, poste)"),
    sort_by: str = Query(None, description="Champ de tri (first_name, last_name, email, badge_id, position, created_at, updated_at)"),
    sort_order: str = Query("asc", description="Direction du tri (asc ou desc)"),
) -> Any:
    """
    Retrieve employees with enriched data.
    """
    employee_data = crud.employee.get_multi_paginated(
        db,
        skip=skip,
        limit=limit,
        organization_id=organization_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
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

@router.get(
    "/{employee_id}",
    response_model=schemas.Employee,
    summary="Récupérer un employé",
    description="Récupère les détails d'un employé spécifique. Requiert la permission `employee:read`.",
    dependencies=[Depends(PermissionChecker(["employee:read"]))],
)
def read_employee(
    *,
    db: Session = Depends(get_db),
    employee_id: str,
) -> Any:
    """
    Retrieve a specific employee by ID.
    """
    employee = crud.employee.get(db=db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"L'employé avec l'ID {employee_id} n'a pas été trouvé.",
        )
    return employee

@router.put(
    "/{employee_id}",
    response_model=schemas.Employee,
    summary="Mettre à jour un employé",
    description="Met à jour les informations d'un employé existant. Requiert la permission `employee:update`.",
    dependencies=[Depends(PermissionChecker(["employee:update"]))],
)
def update_employee(
    *,
    db: Session = Depends(get_db),
    employee_id: str,
    employee_in: schemas.EmployeeUpdate,
) -> Any:
    """
    Update an employee.
    """
    employee = crud.employee.get(db=db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"L'employé avec l'ID {employee_id} n'a pas été trouvé.",
        )

    employee = crud.employee.update(db=db, db_obj=employee, obj_in=employee_in)

    # Re-fetch with relationships for the response
    db.refresh(employee)
    enriched_employee = crud.employee.get(db, id=employee.id)

    return enriched_employee

@router.delete(
    "/{employee_id}",
    response_model=schemas.Employee,
    summary="Supprimer un employé",
    description="Supprime un employé. Requiert la permission `employee:delete`.",
    dependencies=[Depends(PermissionChecker(["employee:delete"]))],
)
def delete_employee(
    *,
    db: Session = Depends(get_db),
    employee_id: str,
) -> Any:
    """
    Delete an employee.
    """
    # Fetch employee with relationships before deletion
    employee = crud.employee.get(db=db, id=employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"L'employé avec l'ID {employee_id} n'a pas été trouvé.",
        )

    # Build response data while session is still active
    response_data = schemas.Employee.model_validate(employee)

    # Now delete the employee
    crud.employee.remove(db=db, id=employee_id)

    return response_data