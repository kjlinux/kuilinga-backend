from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.dependencies import get_db, get_current_active_user, require_role
from app.models.user import UserRole

router = APIRouter()

@router.get(
    "/",
    response_model=List[schemas.Device],
    summary="Lister les terminaux de l'organisation",
    description="Récupère une liste de terminaux pour l'organisation de l'utilisateur. **Requiert le rôle 'manager'.**",
)
def read_devices(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Nombre de terminaux à sauter"),
    limit: int = Query(100, description="Nombre maximum de terminaux à retourner"),
    current_user: models.user = Depends(require_role(UserRole.MANAGER)),
) -> Any:
    devices = crud.device.get_multi_by_organization(
        db, organization_id=current_user.organization_id, skip=skip, limit=limit
    )
    return devices

@router.post(
    "/",
    response_model=schemas.Device,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouveau terminal",
    description="Crée un nouveau terminal (ex: pointeuse) pour une organisation. **Requiert le rôle 'manager'.**",
    responses={
        403: {"description": "Impossible de créer un terminal pour une autre organisation."},
    },
)
def create_device(
    *,
    db: Session = Depends(get_db),
    device_in: schemas.DeviceCreate,
    current_user: models.user = Depends(require_role(UserRole.MANAGER)),
) -> Any:
    if not current_user.is_superuser and current_user.organization_id != device_in.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de créer un terminal pour une autre organisation.",
        )
    device = crud.device.create(db=db, obj_in=device_in)
    return device

@router.get(
    "/{device_id}",
    response_model=schemas.Device,
    summary="Lire un terminal par ID",
    description="Récupère les informations d'un terminal spécifique par son ID.",
    responses={
        403: {"description": "Permissions insuffisantes"},
        404: {"description": "Terminal non trouvé"},
    },
)
def read_device(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    current_user: models.user = Depends(get_current_active_user),
) -> Any:
    device = crud.device.get(db=db, id=device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Terminal non trouvé")
    
    if not current_user.is_superuser and current_user.organization_id != device.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")

    return device

@router.put(
    "/{device_id}",
    response_model=schemas.Device,
    summary="Mettre à jour un terminal",
    description="Met à jour les informations d'un terminal. **Requiert le rôle 'manager'.**",
    responses={
        403: {"description": "Permissions insuffisantes"},
        404: {"description": "Terminal non trouvé"},
    },
)
def update_device(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    device_in: schemas.DeviceUpdate,
    current_user: models.user = Depends(require_role(UserRole.MANAGER)),
) -> Any:
    device = crud.device.get(db=db, id=device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Terminal non trouvé")

    if not current_user.is_superuser and current_user.organization_id != device.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")

    device = crud.device.update(db=db, db_obj=device, obj_in=device_in)
    return device

@router.delete(
    "/{device_id}",
    response_model=schemas.Device,
    summary="Supprimer un terminal",
    description="Supprime un terminal. **Requiert le rôle 'admin'.**",
    responses={
        403: {"description": "Permissions insuffisantes"},
        404: {"description": "Terminal non trouvé"},
    },
)
def delete_device(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    current_user: models.user = Depends(require_role(UserRole.ADMIN)),
) -> Any:
    device = crud.device.get(db=db, id=device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Terminal non trouvé")

    if not current_user.is_superuser and current_user.organization_id != device.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")

    deleted_device = crud.device.remove(db=db, id=device_id)
    return deleted_device