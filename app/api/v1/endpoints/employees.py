from typing import List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app import dependencies
from app.models.user import UserRole

router = APIRouter()

@router.get("/", response_model=List[schemas.Employee])
def read_employees(
    db: Session = Depends(dependencies.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(dependencies.get_current_active_user),
) -> Any:
    """
    Récupérer la liste des employés.
    - Les super-utilisateurs voient tous les employés.
    - Les managers voient les employés de leur organisation.
    """
    if crud.user.is_superuser(current_user):
        employees = crud.employee.get_multi(db, skip=skip, limit=limit)
    else:
        # Assuming a manager is linked to an organization via their employee profile
        if not current_user.employee:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not an employee")
        employees = crud.employee.get_multi_by_organization(
            db, organization_id=current_user.employee.organization_id, skip=skip, limit=limit
        )
    return employees

@router.post("/", response_model=schemas.Employee, status_code=status.HTTP_201_CREATED)
def create_employee(
    *,
    db: Session = Depends(dependencies.get_db),
    employee_in: schemas.EmployeeCreate,
    current_user: models.User = Depends(dependencies.require_role(UserRole.ADMIN, UserRole.MANAGER)),
) -> Any:
    """
    Créer un nouvel employé.
    - Les admins et managers peuvent créer des employés.
    """
    if not crud.user.is_superuser(current_user):
        if not current_user.employee or current_user.employee.organization_id != employee_in.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create employees for other organizations")
    employee = crud.employee.create(db=db, obj_in=employee_in)
    return employee

@router.get("/{employee_id}", response_model=schemas.Employee)
def read_employee(
    *,
    db: Session = Depends(dependencies.get_db),
    employee_id: UUID,
    current_user: models.User = Depends(dependencies.get_current_active_user),
) -> Any:
    """
    Récupérer un employé par son ID.
    """
    employee = crud.employee.get(db=db, id=employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    if not crud.user.is_superuser(current_user):
        if not current_user.employee or current_user.employee.organization_id != employee.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return employee

@router.put("/{employee_id}", response_model=schemas.Employee)
def update_employee(
    *,
    db: Session = Depends(dependencies.get_db),
    employee_id: UUID,
    employee_in: schemas.EmployeeUpdate,
    current_user: models.User = Depends(dependencies.require_role(UserRole.ADMIN, UserRole.MANAGER)),
) -> Any:
    """
    Mettre à jour un employé.
    """
    employee = crud.employee.get(db=db, id=employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    if not crud.user.is_superuser(current_user):
        if not current_user.employee or current_user.employee.organization_id != employee.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    employee = crud.employee.update(db=db, db_obj=employee, obj_in=employee_in)
    return employee

@router.delete("/{employee_id}", response_model=schemas.Employee)
def delete_employee(
    *,
    db: Session = Depends(dependencies.get_db),
    employee_id: UUID,
    current_user: models.User = Depends(dependencies.require_role(UserRole.ADMIN, UserRole.MANAGER)),
) -> Any:
    """
    Supprimer un employé.
    """
    employee = crud.employee.get(db=db, id=employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    if not crud.user.is_superuser(current_user):
        if not current_user.employee or current_user.employee.organization_id != employee.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    employee = crud.employee.delete(db=db, id=employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee