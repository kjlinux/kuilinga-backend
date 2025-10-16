from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.dependencies import get_db, get_current_active_user, require_role

router = APIRouter()

def enrich_device_response(db: Session, device: models.Device) -> schemas.Device:
    """
    Enrich the device object with organization, site, and attendance stats.
    """
    device_schema = schemas.Device.from_orm(device)

    # Get attendance stats
    last_attendance = crud.attendance.get_last_for_device(db, device_id=device.id)
    if last_attendance:
        device_schema.last_attendance_timestamp = last_attendance.timestamp

    device_schema.daily_attendance_count = crud.attendance.count_today_for_device(db, device_id=device.id)

    return device_schema

@router.get(
    "/",
    response_model=schemas.PaginatedResponse[schemas.Device],
    summary="Lister les terminaux de l'organisation",
    dependencies=[Depends(PermissionChecker(["device:read"]))],
)
def read_devices(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Nombre de terminaux à sauter"),
    limit: int = Query(100, description="Nombre maximum de terminaux à retourner"),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    device_data = crud.device.get_multi_paginated_by_org(
        db, organization_id=current_user.organization_id, skip=skip, limit=limit
    )

    enriched_items = [enrich_device_response(db, device) for device in device_data["items"]]

    return {
        "items": enriched_items,
        "total": device_data["total"],
        "skip": skip,
        "limit": limit,
    }

@router.post(
    "/",
    response_model=schemas.Device,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouveau terminal",
    dependencies=[Depends(PermissionChecker(["device:create"]))],
)
def create_device(
    *,
    db: Session = Depends(get_db),
    device_in: schemas.DeviceCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    if not current_user.is_superuser and current_user.organization_id != device_in.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de créer un terminal pour une autre organisation.",
        )
    device = crud.device.create(db=db, obj_in=device_in)
    db.refresh(device, ["organization", "site"])
    return enrich_device_response(db, device)

@router.get(
    "/{device_id}",
    response_model=schemas.Device,
    summary="Lire un terminal par ID",
    dependencies=[Depends(PermissionChecker(["device:read"]))],
)
def read_device(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    device = crud.device.get(db=db, id=device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Terminal non trouvé")
    
    if not current_user.is_superuser and current_user.organization_id != device.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")

    return enrich_device_response(db, device)

@router.put(
    "/{device_id}",
    response_model=schemas.Device,
    summary="Mettre à jour un terminal",
    dependencies=[Depends(PermissionChecker(["device:update"]))],
)
def update_device(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    device_in: schemas.DeviceUpdate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    device = crud.device.get(db=db, id=device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Terminal non trouvé")

    if not current_user.is_superuser and current_user.organization_id != device.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")

    device = crud.device.update(db=db, db_obj=device, obj_in=device_in)
    db.refresh(device, ["organization", "site"])
    return enrich_device_response(db, device)

@router.delete(
    "/{device_id}",
    response_model=schemas.Device,
    summary="Supprimer un terminal",
    dependencies=[Depends(PermissionChecker(["device:delete"]))],
)
def delete_device(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    device = crud.device.get(db=db, id=device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Terminal non trouvé")

    if not current_user.is_superuser and current_user.organization_id != device.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")

    enriched_device = enrich_device_response(db, device)
    crud.device.remove(db=db, id=device_id)
    return enriched_device