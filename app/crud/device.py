from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate

class CRUDDevice(CRUDBase[Device, DeviceCreate, DeviceUpdate]):
    def get_by_serial_number(self, db: Session, *, serial_number: str) -> Optional[Device]:
        return db.query(self.model).filter(Device.serial_number == serial_number).first()

    def get_multi_by_organization(
        self, db: Session, *, organization_id: str, skip: int = 0, limit: int = 100
    ) -> List[Device]:
        return (
            db.query(self.model)
            .filter(Device.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

device = CRUDDevice(Device)