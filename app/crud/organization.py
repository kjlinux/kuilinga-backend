from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.crud.base import CRUDBase
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate


class CRUDOrganization(CRUDBase[Organization, OrganizationCreate, OrganizationUpdate]):
    """Opérations CRUD pour les organisations"""
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[Organization]:
        """Récupérer une organisation par nom"""
        return db.query(Organization).filter(Organization.name == name).first()
    
    def get_active(
        self, 
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Organization]:
        """Récupérer les organisations actives"""
        return db.query(Organization).filter(
            Organization.is_active == True
        ).offset(skip).limit(limit).all()
    
    def get_by_plan(
        self,
        db: Session,
        *,
        plan: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Organization]:
        """Récupérer les organisations par plan"""
        return db.query(Organization).filter(
            Organization.plan == plan
        ).offset(skip).limit(limit).all()
    
    def search(
        self,
        db: Session,
        *,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Organization]:
        """Rechercher des organisations"""
        search_pattern = f"%{search_term}%"
        return db.query(Organization).filter(
            (Organization.name.ilike(search_pattern)) |
            (Organization.description.ilike(search_pattern)) |
            (Organization.email.ilike(search_pattern))
        ).offset(skip).limit(limit).all()
    
    def activate(self, db: Session, *, organization_id: UUID) -> Organization:
        """Activer une organisation"""
        org = self.get(db, id=organization_id)
        if org:
            org.is_active = True
            db.commit()
            db.refresh(org)
        return org
    
    def deactivate(self, db: Session, *, organization_id: UUID) -> Organization:
        """Désactiver une organisation"""
        org = self.get(db, id=organization_id)
        if org:
            org.is_active = False
            db.commit()
            db.refresh(org)
        return org
    
    def count_active(self, db: Session) -> int:
        """Compter les organisations actives"""
        return db.query(func.count(Organization.id)).filter(
            Organization.is_active == True
        ).scalar()


# Instance globale
organization = CRUDOrganization(Organization)