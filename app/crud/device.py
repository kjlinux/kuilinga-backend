from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, asc, desc
from app.crud.base import CRUDBase
from app.models.device import Device, DeviceStatus
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceHeartbeatUpdate

class CRUDDevice(CRUDBase[Device, DeviceCreate, DeviceUpdate]):
    def get_by_serial_number(self, db: Session, *, serial_number: str) -> Optional[Device]:
        return db.query(self.model).filter(Device.serial_number == serial_number).first()

    # Alias for MQTT client compatibility
    def get_by_serial(self, db: Session, *, serial_number: str) -> Optional[Device]:
        return self.get_by_serial_number(db, serial_number=serial_number)

    def get_multi_paginated(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        organization_id: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "asc"
    ) -> Dict[str, Any]:
        query = db.query(self.model).options(
            joinedload(Device.organization),
            joinedload(Device.site)
        )

        # Filter by organization if provided
        if organization_id:
            query = query.filter(Device.organization_id == organization_id)

        # Search functionality
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Device.serial_number.ilike(search_filter),
                    Device.name.ilike(search_filter),
                    Device.device_type.ilike(search_filter),
                    Device.location.ilike(search_filter)
                )
            )

        total = query.count()

        # Sort functionality
        if sort_by:
            valid_columns = ["serial_number", "name", "device_type", "location", "created_at", "updated_at"]
            if sort_by in valid_columns:
                column = getattr(Device, sort_by)
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
            else:
                query = query.order_by(Device.serial_number)
        else:
            query = query.order_by(Device.serial_number)

        items = query.offset(skip).limit(limit).all()
        return {"items": items, "total": total}

    def get_multi_paginated_by_org(
        self, db: Session, *, organization_id: str, skip: int = 0, limit: int = 100
    ) -> Dict[str, Any]:
        # Use the new method for backward compatibility
        return self.get_multi_paginated(
            db, skip=skip, limit=limit, organization_id=organization_id
        )

    def count_by_site(self, db: Session, *, site_id: str) -> int:
        return db.query(self.model).filter(Device.site_id == site_id).count()

    def update_heartbeat(
        self,
        db: Session,
        *,
        device: Device,
        heartbeat_data: DeviceHeartbeatUpdate
    ) -> Device:
        """
        Met à jour le device avec les données du heartbeat MQTT.
        Passe automatiquement le statut à ONLINE.
        """
        device.status = DeviceStatus.ONLINE
        device.last_seen_at = heartbeat_data.last_seen_at

        if heartbeat_data.firmware_version is not None:
            device.firmware_version = heartbeat_data.firmware_version
        if heartbeat_data.battery_level is not None:
            device.battery_level = heartbeat_data.battery_level
        if heartbeat_data.wifi_rssi is not None:
            device.wifi_rssi = heartbeat_data.wifi_rssi

        db.add(device)
        db.commit()
        db.refresh(device)
        return device

    def update_last_seen(self, db: Session, *, device: Device) -> Device:
        """
        Met à jour uniquement last_seen_at (pour les pointages sans heartbeat complet).
        """
        device.last_seen_at = datetime.now(timezone.utc)
        device.status = DeviceStatus.ONLINE
        db.add(device)
        db.commit()
        db.refresh(device)
        return device

    def get_stale_devices(
        self,
        db: Session,
        *,
        timeout_minutes: int = 5
    ) -> List[Device]:
        """
        Retourne les devices ONLINE dont le last_seen_at dépasse le timeout.
        Ces devices doivent être marqués OFFLINE.
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)

        return db.query(self.model).filter(
            Device.status == DeviceStatus.ONLINE,
            or_(
                Device.last_seen_at == None,  # Jamais vu
                Device.last_seen_at < cutoff_time  # Pas vu depuis timeout
            )
        ).all()

    def mark_devices_offline(
        self,
        db: Session,
        *,
        timeout_minutes: int = 5
    ) -> int:
        """
        Marque OFFLINE tous les devices sans heartbeat récent.
        Retourne le nombre de devices mis à jour.
        """
        stale_devices = self.get_stale_devices(db, timeout_minutes=timeout_minutes)
        count = 0

        for device in stale_devices:
            device.status = DeviceStatus.OFFLINE
            db.add(device)
            count += 1

        if count > 0:
            db.commit()

        return count

    def get_devices_by_status(
        self,
        db: Session,
        *,
        status: DeviceStatus,
        organization_id: Optional[str] = None
    ) -> List[Device]:
        """
        Retourne tous les devices avec un statut donné.
        """
        query = db.query(self.model).filter(Device.status == status)

        if organization_id:
            query = query.filter(Device.organization_id == organization_id)

        return query.all()


device = CRUDDevice(Device)