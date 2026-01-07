from typing import Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, asc, desc
from app.crud.base import CRUDBase
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate

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

device = CRUDDevice(Device)