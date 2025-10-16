from typing import Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from app.crud.base import CRUDBase
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate

class CRUDDevice(CRUDBase[Device, DeviceCreate, DeviceUpdate]):
    def get_by_serial_number(self, db: Session, *, serial_number: str) -> Optional[Device]:
        return db.query(self.model).filter(Device.serial_number == serial_number).first()

    def get_multi_paginated_by_org(
        self, db: Session, *, organization_id: str, skip: int = 0, limit: int = 100
    ) -> Dict[str, Any]:
        query = (
            db.query(self.model)
            .filter(Device.organization_id == organization_id)
            .options(
                joinedload(Device.organization),
                joinedload(Device.site)
            )
        )
        total = query.count()
        items = query.order_by(Device.serial_number).offset(skip).limit(limit).all()
        return {"items": items, "total": total}

    def count_by_site(self, db: Session, *, site_id: str) -> int:
        return db.query(self.model).filter(Device.site_id == site_id).count()

device = CRUDDevice(Device)