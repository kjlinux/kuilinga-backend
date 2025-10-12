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
