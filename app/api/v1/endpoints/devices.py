from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.crud.device import device as device_crud
from app.schemas.device import (
    Device,
    DeviceCreate,
    DeviceUpdate,
    DeviceList,
    DevicePing,
    DeviceStats
)
from app.models.user import User, UserRole
from app.models.device import DeviceType
from app.models.attendance import Attendance
from app.dependencies import get_current_active_user, require_role

router = APIRouter()


@router.get("/", response_model=DeviceList)
def read_devices(
    db: Session = Depends(get_db),
    organization_id: int = Query(..., description="ID de l'organisation"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    is_online: Optional[bool] = None,
    device_type: Optional[DeviceType] = None,
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.ADMIN)),
) -> DeviceList:
    """
    Récupérer la liste des devices
    """
    devices = device_crud.get_by_organization(
        db,
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        is_online=is_online,
        device_type=device_type
    )
    
    total = device_crud.count_by_organization(db, organization_id=organization_id)
    
    return {
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit,
        "devices": devices
    }


@router.get("/online", response_model=List[Device])
def read_online_devices(
    db: Session = Depends(get_db),
    organization_id: int = Query(..., description="ID de l'organisation"),
    current_user: User = Depends(get_current_active_user),
) -> List[Device]:
    """
    Récupérer les devices en ligne
    """
    devices = device_crud.get_online_devices(
        db,
        organization_id=organization_id
    )
    return devices


@router.get("/{device_id}", response_model=Device)
def read_device(
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Device:
    """
    Récupérer un device par ID
    """
    device = device_crud.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device non trouvé"
        )
    return device


@router.get("/serial/{serial_number}", response_model=Device)
def read_device_by_serial(
    serial_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Device:
    """
    Récupérer un device par numéro de série
    """
    device = device_crud.get_by_serial(db, serial_number=serial_number)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device non trouvé"
        )
    return device


@router.get("/{device_id}/stats", response_model=DeviceStats)
def read_device_stats(
    device_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.ADMIN)),
) -> DeviceStats:
    """
    Récupérer les statistiques d'un device
    """
    device = device_crud.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device non trouvé"
        )
    
    # Compter les pointages totaux
    total_attendances = db.query(func.count(Attendance.id)).filter(
        Attendance.device_id == device_id
    ).scalar()
    
    # Pointages aujourd'hui
    today = datetime.now().date()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())
    
    attendances_today = db.query(func.count(Attendance.id)).filter(
        Attendance.device_id == device_id,
        Attendance.timestamp >= start,
        Attendance.timestamp <= end
    ).scalar()
    
    # Dernier pointage
    last_attendance = db.query(Attendance).filter(
        Attendance.device_id == device_id
    ).order_by(Attendance.timestamp.desc()).first()
    
    return {
        "device_id": device.id,
        "device_name": device.name,
        "total_attendances": total_attendances or 0,
        "attendances_today": attendances_today or 0,
        "last_attendance": last_attendance.timestamp if last_attendance else None,
        "uptime_percentage": 99.5  # À calculer selon la logique métier
    }


@router.post("/", response_model=Device, status_code=status.HTTP_201_CREATED)
def create_device(
    *,
    db: Session = Depends(get_db),
    device_in: DeviceCreate,
    current_user: User = Depends(require_role(UserRole.INTEGRATOR, UserRole.ADMIN)),
) -> Device:
    """
    Créer un nouveau device
    """
    # Vérifier si le serial existe déjà
    existing_device = device_crud.get_by_serial(db, serial_number=device_in.serial_number)
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un device avec ce numéro de série existe déjà"
        )
    
    device = device_crud.create(db, obj_in=device_in)
    return device


@router.post("/{device_id}/ping", response_model=Device)
def ping_device(
    *,
    db: Session = Depends(get_db),
    device_id: UUID,
    ping_data: DevicePing,
    current_user: User = Depends(get_current_active_user),
) -> Device:
    """
    Enregistrer un ping de device (heartbeat)
    """
    device = device_crud.update_ping(
        db,
        device_id=device_id,
        timestamp=ping_data.timestamp
    )
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device non trouvé"
        )
    
    return device


@router.post("/{device_id}/offline", response_model=Device)
def mark_device_offline(
    *,
    db: Session = Depends(get_db),
    device_id: UUID,
    current_user: User = Depends(require_role(UserRole.INTEGRATOR, UserRole.ADMIN)),
) -> Device:
    """
    Marquer un device comme hors ligne
    """
    device = device_crud.mark_offline(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device non trouvé"
        )
    return device


@router.put("/{device_id}", response_model=Device)
def update_device(
    *,
    db: Session = Depends(get_db),
    device_id: UUID,
    device_in: DeviceUpdate,
    current_user: User = Depends(require_role(UserRole.INTEGRATOR, UserRole.ADMIN)),
) -> Device:
    """
    Mettre à jour un device
    """
    device = device_crud.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device non trouvé"
        )
    
    device = device_crud.update(db, db_obj=device, obj_in=device_in)
    return device


@router.put("/{device_id}/firmware", response_model=Device)
def update_device_firmware(
    *,
    db: Session = Depends(get_db),
    device_id: UUID,
    firmware_version: str,
    current_user: User = Depends(require_role(UserRole.INTEGRATOR, UserRole.ADMIN)),
) -> Device:
    """
    Mettre à jour la version firmware d'un device
    """
    device = device_crud.update_firmware(
        db,
        device_id=device_id,
        firmware_version=firmware_version
    )
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device non trouvé"
        )
    
    return device


@router.delete("/{device_id}", response_model=Device)
def delete_device(
    *,
    db: Session = Depends(get_db),
    device_id: UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> Device:
    """
    Supprimer un device
    """
    device = device_crud.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device non trouvé"
        )
    
    device = device_crud.delete(db, id=device_id)
    return device