from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.dependencies import get_db, get_current_active_user, require_role
from app.models.user import UserRole

router = APIRouter()

@router.get(
    "/",
    response_model=List[schemas.Employee],
    summary="Lister les employés",
    description="Récupère une liste d'employés. Un admin voit tous les employés, un manager ne voit que ceux de son organisation.",
)
def read_employees(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Nombre d'employés à sauter"),
    limit: int = Query(100, description="Nombre maximum d'employés à retourner"),
    current_user: models.user = Depends(get_current_active_user),
) -> Any:
    if current_user.is_superuser:
        employees = crud.employee.get_multi(db, skip=skip, limit=limit)
    else:
        employees = crud.employee.get_multi_by_organization(
            db, organization_id=current_user.organization_id, skip=skip, limit=limit
        )
    return employees

@router.post(
    "/",
    response_model=schemas.Employee,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un employé",
    description="Crée un nouvel employé. **Requiert le rôle 'manager'.** Un manager ne peut créer un employé que dans sa propre organisation.",
    responses={
        403: {"description": "Impossible de créer un employé pour une autre organisation."},
    },
)
def create_employee(
    *,
    db: Session = Depends(get_db),
    employee_in: schemas.EmployeeCreate,
    current_user: models.user = Depends(require_role(UserRole.MANAGER)),
) -> Any:
    if not current_user.is_superuser and current_user.organization_id != employee_in.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de créer un employé pour une autre organisation.",
        )
    employee = crud.employee.create(db=db, obj_in=employee_in)
    return employee

@router.get(
    "/{employee_id}",
    response_model=schemas.Employee,
    summary="Lire un employé par ID",
    description="Récupère les informations d'un employé spécifique par son ID.",
    responses={
        403: {"description": "Permissions insuffisantes"},
        404: {"description": "Employé non trouvé"},
    },
)
def read_employee(
    *,
    db: Session = Depends(get_db),
    employee_id: str,
    current_user: models.user = Depends(get_current_active_user),
) -> Any:
    employee = crud.employee.get(db=db, id=employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")

    if not current_user.is_superuser and current_user.organization_id != employee.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")

    return employee

@router.put(
    "/{employee_id}",
    response_model=schemas.Employee,
    summary="Mettre à jour un employé",
    description="Met à jour les informations d'un employé. **Requiert le rôle 'manager'.**",
    responses={
        403: {"description": "Permissions insuffisantes"},
        404: {"description": "Employé non trouvé"},
    },
)
def update_employee(
    *,
    db: Session = Depends(get_db),
    employee_id: str,
    employee_in: schemas.EmployeeUpdate,
    current_user: models.user = Depends(require_role(UserRole.MANAGER)),
) -> Any:
    employee = crud.employee.get(db=db, id=employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")

    if not current_user.is_superuser and current_user.organization_id != employee.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")

    employee = crud.employee.update(db=db, db_obj=employee, obj_in=employee_in)
    return employee

@router.delete(
    "/{employee_id}",
    response_model=schemas.Employee,
    summary="Supprimer un employé",
    description="Supprime un employé. **Requiert le rôle 'manager'.**",
    responses={
        403: {"description": "Permissions insuffisantes"},
        404: {"description": "Employé non trouvé"},
    },
)
def delete_employee(
    *,
    db: Session = Depends(get_db),
    employee_id: str,
    current_user: models.user = Depends(require_role(UserRole.MANAGER)),
) -> Any:
    employee = crud.employee.get(db=db, id=employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé non trouvé")

    if not current_user.is_superuser and current_user.organization_id != employee.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")

    deleted_employee = crud.employee.remove(db=db, id=employee_id)
    return deleted_employee