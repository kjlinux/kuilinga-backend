from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.dependencies import get_db, get_current_active_user, require_role, PermissionChecker
from app.services.mqtt_client import mqtt_client
from app.schemas.device_command import (
    DeviceCommandRequest,
    DeviceCommandResponse,
    DeviceCommandType,
    DeviceBulkCommandRequest,
    DeviceBulkCommandResponse,
    COMMAND_TYPE_TO_CODE,
)

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
    search: str = Query(None, description="Recherche textuelle (numéro de série, nom, type, localisation)"),
    sort_by: str = Query(None, description="Champ de tri (serial_number, name, device_type, location, created_at, updated_at)"),
    sort_order: str = Query("asc", description="Direction du tri (asc ou desc)"),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    device_data = crud.device.get_multi_paginated(
        db,
        organization_id=current_user.organization_id,
        skip=skip,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
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


# ============================================================================
# ENDPOINTS DE COMMANDE IoT
# ============================================================================

@router.post(
    "/{device_id}/command",
    response_model=DeviceCommandResponse,
    summary="Envoyer une commande à un terminal",
    description="""
    Envoie une commande administrative à un terminal IoT via MQTT.

    **Commandes disponibles:**
    - `reset` (0x108070): Réinitialiser l'appareil
    - `reboot` (0x108090): Redémarrer l'appareil
    - `sleep` (0x1080B0): Mettre l'appareil en veille
    - `status` (0x100010): Demander le statut de l'appareil

    Le code hexadécimal correspondant est envoyé à l'appareil via MQTT.
    """,
    dependencies=[Depends(PermissionChecker(["device:command"]))],
)
def send_device_command(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    command_request: DeviceCommandRequest,
    current_user: models.User = Depends(get_current_active_user),
) -> DeviceCommandResponse:
    """Envoie une commande à un terminal spécifique."""
    device = crud.device.get(db=db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Terminal non trouvé"
        )

    if not current_user.is_superuser and current_user.organization_id != device.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes"
        )

    # Vérifier la connexion MQTT
    if not mqtt_client.is_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service MQTT non disponible"
        )

    # Envoyer la commande
    command_code = COMMAND_TYPE_TO_CODE[command_request.command]
    success = mqtt_client.send_command(device.serial_number, command_request.command)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Échec de l'envoi de la commande"
        )

    return DeviceCommandResponse(
        success=True,
        device_id=device.id,
        device_serial=device.serial_number,
        command=command_request.command.value,
        command_code=command_code.value,
        message=f"Commande {command_request.command.value.upper()} envoyée au terminal {device.serial_number}"
    )


@router.post(
    "/{device_id}/reboot",
    response_model=DeviceCommandResponse,
    summary="Redémarrer un terminal",
    description="Raccourci pour envoyer la commande REBOOT (0x108090) à un terminal.",
    dependencies=[Depends(PermissionChecker(["device:command"]))],
)
def reboot_device(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    current_user: models.User = Depends(get_current_active_user),
) -> DeviceCommandResponse:
    """Redémarre un terminal."""
    return send_device_command(
        db=db,
        device_id=device_id,
        command_request=DeviceCommandRequest(command=DeviceCommandType.REBOOT),
        current_user=current_user
    )


@router.post(
    "/{device_id}/reset",
    response_model=DeviceCommandResponse,
    summary="Réinitialiser un terminal",
    description="Raccourci pour envoyer la commande RESET (0x108070) à un terminal.",
    dependencies=[Depends(PermissionChecker(["device:command"]))],
)
def reset_device(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    current_user: models.User = Depends(get_current_active_user),
) -> DeviceCommandResponse:
    """Réinitialise un terminal."""
    return send_device_command(
        db=db,
        device_id=device_id,
        command_request=DeviceCommandRequest(command=DeviceCommandType.RESET),
        current_user=current_user
    )


@router.post(
    "/{device_id}/sleep",
    response_model=DeviceCommandResponse,
    summary="Mettre un terminal en veille",
    description="Raccourci pour envoyer la commande SLEEP (0x1080B0) à un terminal.",
    dependencies=[Depends(PermissionChecker(["device:command"]))],
)
def sleep_device(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    current_user: models.User = Depends(get_current_active_user),
) -> DeviceCommandResponse:
    """Met un terminal en veille."""
    return send_device_command(
        db=db,
        device_id=device_id,
        command_request=DeviceCommandRequest(command=DeviceCommandType.SLEEP),
        current_user=current_user
    )


@router.post(
    "/{device_id}/status",
    response_model=DeviceCommandResponse,
    summary="Demander le statut d'un terminal",
    description="Raccourci pour envoyer la commande STATUS (0x100010) à un terminal.",
    dependencies=[Depends(PermissionChecker(["device:command"]))],
)
def request_device_status(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    current_user: models.User = Depends(get_current_active_user),
) -> DeviceCommandResponse:
    """Demande le statut d'un terminal."""
    return send_device_command(
        db=db,
        device_id=device_id,
        command_request=DeviceCommandRequest(command=DeviceCommandType.STATUS),
        current_user=current_user
    )


@router.post(
    "/bulk/command",
    response_model=DeviceBulkCommandResponse,
    summary="Envoyer une commande à plusieurs terminaux",
    description="""
    Envoie une commande administrative à plusieurs terminaux IoT en une seule requête.

    Utile pour les opérations de maintenance groupées.
    """,
    dependencies=[Depends(PermissionChecker(["device:command"]))],
)
def send_bulk_command(
    *,
    db: Session = Depends(get_db),
    bulk_request: DeviceBulkCommandRequest,
    current_user: models.User = Depends(get_current_active_user),
) -> DeviceBulkCommandResponse:
    """Envoie une commande à plusieurs terminaux."""
    if not mqtt_client.is_connected():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service MQTT non disponible"
        )

    results: List[DeviceCommandResponse] = []
    successful = 0
    failed = 0

    command_code = COMMAND_TYPE_TO_CODE[bulk_request.command]

    for device_id in bulk_request.device_ids:
        device = crud.device.get(db=db, id=device_id)

        if not device:
            results.append(DeviceCommandResponse(
                success=False,
                device_id=device_id,
                device_serial="INCONNU",
                command=bulk_request.command.value,
                command_code=command_code.value,
                message=f"Terminal {device_id} non trouvé"
            ))
            failed += 1
            continue

        if not current_user.is_superuser and current_user.organization_id != device.organization_id:
            results.append(DeviceCommandResponse(
                success=False,
                device_id=device_id,
                device_serial=device.serial_number,
                command=bulk_request.command.value,
                command_code=command_code.value,
                message="Permissions insuffisantes"
            ))
            failed += 1
            continue

        success = mqtt_client.send_command(device.serial_number, bulk_request.command)

        if success:
            results.append(DeviceCommandResponse(
                success=True,
                device_id=device.id,
                device_serial=device.serial_number,
                command=bulk_request.command.value,
                command_code=command_code.value,
                message=f"Commande {bulk_request.command.value.upper()} envoyée"
            ))
            successful += 1
        else:
            results.append(DeviceCommandResponse(
                success=False,
                device_id=device.id,
                device_serial=device.serial_number,
                command=bulk_request.command.value,
                command_code=command_code.value,
                message="Échec de l'envoi"
            ))
            failed += 1

    return DeviceBulkCommandResponse(
        success=failed == 0,
        total_devices=len(bulk_request.device_ids),
        successful=successful,
        failed=failed,
        results=results
    )


@router.get(
    "/mqtt/status",
    summary="Vérifier le statut de la connexion MQTT",
    description="Retourne l'état de la connexion au broker MQTT.",
    dependencies=[Depends(PermissionChecker(["device:read"]))],
)
def get_mqtt_status(
    current_user: models.User = Depends(get_current_active_user),
) -> dict:
    """Vérifie le statut de la connexion MQTT."""
    return {
        "connected": mqtt_client.is_connected(),
        "broker_host": mqtt_client.client._host if hasattr(mqtt_client.client, '_host') else None,
        "broker_port": mqtt_client.client._port if hasattr(mqtt_client.client, '_port') else None,
    }