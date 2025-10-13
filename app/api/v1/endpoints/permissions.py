from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.dependencies import get_db, PermissionChecker

router = APIRouter()

@router.post(
    "/",
    response_model=schemas.Permission,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker(["permission:create"]))],
)
def create_permission(*, db: Session = Depends(get_db), permission_in: schemas.PermissionCreate):
    """
    Create a new permission. Requires permission: `permission:create`.
    """
    permission = crud.permission.create(db=db, obj_in=permission_in)
    return permission

@router.get(
    "/",
    response_model=List[schemas.Permission],
    dependencies=[Depends(PermissionChecker(["permission:read"]))],
)
def read_permissions(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """
    Retrieve permissions. Requires permission: `permission:read`.
    """
    permissions = crud.permission.get_multi(db, skip=skip, limit=limit)
    return permissions

@router.get(
    "/{permission_id}",
    response_model=schemas.Permission,
    dependencies=[Depends(PermissionChecker(["permission:read"]))],
)
def read_permission(*, db: Session = Depends(get_db), permission_id: str):
    """
    Get a permission by ID. Requires permission: `permission:read`.
    """
    permission = crud.permission.get(db=db, id=permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return permission

@router.put(
    "/{permission_id}",
    response_model=schemas.Permission,
    dependencies=[Depends(PermissionChecker(["permission:update"]))],
)
def update_permission(*, db: Session = Depends(get_db), permission_id: str, permission_in: schemas.PermissionUpdate):
    """
    Update a permission. Requires permission: `permission:update`.
    """
    permission = crud.permission.get(db=db, id=permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    permission = crud.permission.update(db=db, db_obj=permission, obj_in=permission_in)
    return permission

@router.delete(
    "/{permission_id}",
    response_model=schemas.Permission,
    dependencies=[Depends(PermissionChecker(["permission:delete"]))],
)
def delete_permission(*, db: Session = Depends(get_db), permission_id: str):
    """
    Delete a permission. Requires permission: `permission:delete`.
    """
    permission = crud.permission.get(db=db, id=permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    permission = crud.permission.remove(db=db, id=permission_id)
    return permission
