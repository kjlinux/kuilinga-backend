from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, models, schemas
from app.dependencies import get_db, PermissionChecker

router = APIRouter()

@router.post(
    "/",
    response_model=schemas.Role,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker(["role:create"]))],
)
def create_role(*, db: Session = Depends(get_db), role_in: schemas.RoleCreate):
    """
    Create a new role. Requires permission: `role:create`.
    """
    role = crud.role.create(db=db, obj_in=role_in)
    return role

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any
from app import crud, models, schemas
from app.dependencies import get_db, PermissionChecker

@router.get(
    "/",
    response_model=schemas.PaginatedResponse[schemas.Role],
    dependencies=[Depends(PermissionChecker(["role:read"]))],
)
def read_roles(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Nombre de rôles à sauter"),
    limit: int = Query(100, description="Nombre maximum de rôles à retourner"),
) -> Any:
    """
    Retrieve roles. Requires permission: `role:read`.
    """
    role_data = crud.role.get_multi(db, skip=skip, limit=limit)
    return {
        "items": role_data["items"],
        "total": role_data["total"],
        "skip": skip,
        "limit": limit,
    }

@router.post(
    "/{role_id}/permissions/{permission_id}",
    response_model=schemas.Role,
    dependencies=[Depends(PermissionChecker(["role:assign_permission"]))],
)
def assign_permission_to_role(
    *, db: Session = Depends(get_db), role_id: str, permission_id: str
):
    """
    Assign a permission to a role. Requires permission: `role:assign_permission`.
    """
    role = crud.role.get(db=db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    permission = crud.permission.get(db=db, id=permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    role = crud.role.assign_permissions_to_role(db=db, role=role, permissions=[permission])
    return role

@router.get(
    "/{role_id}",
    response_model=schemas.Role,
    dependencies=[Depends(PermissionChecker(["role:read"]))],
)
def read_role(*, db: Session = Depends(get_db), role_id: str):
    """
    Get a role by ID. Requires permission: `role:read`.
    """
    role = crud.role.get(db=db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.put(
    "/{role_id}",
    response_model=schemas.Role,
    dependencies=[Depends(PermissionChecker(["role:update"]))],
)
def update_role(*, db: Session = Depends(get_db), role_id: str, role_in: schemas.RoleUpdate):
    """
    Update a role. Requires permission: `role:update`.
    """
    role = crud.role.get(db=db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    role = crud.role.update(db=db, db_obj=role, obj_in=role_in)
    return role

@router.delete(
    "/{role_id}",
    response_model=schemas.Role,
    dependencies=[Depends(PermissionChecker(["role:delete"]))],
)
def delete_role(*, db: Session = Depends(get_db), role_id: str):
    """
    Delete a role. Requires permission: `role:delete`.
    """
    role = crud.role.get(db=db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    # Build response data while session is still active
    response_data = schemas.Role.model_validate(role)
    crud.role.remove(db=db, id=role_id)
    return response_data
