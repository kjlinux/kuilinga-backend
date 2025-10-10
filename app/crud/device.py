from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.crud.base import CRUDBase
from app.models.device import Device, DeviceStatus, DeviceType
from app.schemas.device import DeviceCreate, DeviceUpdate


class CRUDDevice(CRUDBase[Device, DeviceCreate, DeviceUpdate]):
    """Opérations CRUD pour les devices"""
    
    def get_by_serial(self, db: Session, *, serial_number: str) -> Optional[Device]:
        """Récupérer un device par numéro de série"""
        return db.query(Device).filter(Device.serial_number == serial_number).first()
    
    def get_by_organization(
        self,
        db: Session,
        *,
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
        is_online: Optional[bool] = None,
        device_type: Optional[DeviceType] = None
    ) -> List[Device]:
        """Récupérer les devices d'une organisation"""
        query = db.query(Device).filter(Device.organization_id == organization_id)
        
        if is_online is not None:
            query = query.filter(Device.is_online == is_online)
        
        if device_type:
            query = query.filter(Device.device_type == device_type)
        
        return query.offset(skip).limit(limit).all()
    
    def get_online_devices(
        self,
        db: Session,
        organization_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Device]:
        """Récupérer les devices en ligne"""
        return db.query(Device).filter(
            Device.organization_id == organization_id,
            Device.is_online == True,
            Device.status == DeviceStatus.ACTIVE
        ).offset(skip).limit(limit).all()
    
    def update_ping(
        self,
        db: Session,
        *,
        device_id: UUID,
        timestamp: datetime
    ) -> Optional[Device]:
        """Mettre à jour le dernier ping d'un device"""
        device = self.get(db, id=device_id)
        if device:
            device.last_ping = timestamp.isoformat()
            device.is_online = True
            db.commit()
            db.refresh(device)
        return device
    
    def mark_offline(self, db: Session, *, device_id: UUID) -> Optional[Device]:
        """Marquer un device comme hors ligne"""
        device = self.get(db, id=device_id)
        if device:
            device.is_online = False
            db.commit()
            db.refresh(device)
        return device
    
    def update_firmware(
        self,
        db: Session,
        *,
        device_id: UUID,
        firmware_version: str
    ) -> Optional[Device]:
        """Mettre à jour la version firmware"""
        device = self.get(db, id=device_id)
        if device:
            device.firmware_version = firmware_version
            db.commit()
            db.refresh(device)
        return device
    
    def count_by_organization(self, db: Session, *, organization_id: int) -> int:
        """Compter les devices d'une organisation"""
        return db.query(func.count(Device.id)).filter(
            Device.organization_id == organization_id
        ).scalar()
    
    def count_online(self, db: Session, *, organization_id: int) -> int:
        """Compter les devices en ligne"""
        return db.query(func.count(Device.id)).filter(
            Device.organization_id == organization_id,
            Device.is_online == True
        ).scalar()


# Instance globale
device = CRUDDevice(Device)