from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.crud.base import CRUDBase
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class CRUDEmployee(CRUDBase[Employee, EmployeeCreate, EmployeeUpdate]):
    """Opérations CRUD pour les employés"""
    
    def get_by_badge_id(self, db: Session, *, badge_id: str) -> Optional[Employee]:
        """Récupérer un employé par badge ID"""
        return db.query(Employee).filter(Employee.badge_id == badge_id).first()
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[Employee]:
        """Récupérer un employé par email"""
        return db.query(Employee).filter(Employee.email == email).first()
    
    def get_by_organization(
        self, 
        db: Session, 
        *, 
        organization_id: int,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Employee]:
        """Récupérer les employés d'une organisation"""
        query = db.query(Employee).filter(Employee.organization_id == organization_id)
        
        if is_active is not None:
            query = query.filter(Employee.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def search(
        self,
        db: Session,
        *,
        organization_id: int,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Employee]:
        """Rechercher des employés par nom, email ou badge"""
        search_pattern = f"%{search_term}%"
        return db.query(Employee).filter(
            Employee.organization_id == organization_id,
            (
                Employee.first_name.ilike(search_pattern) |
                Employee.last_name.ilike(search_pattern) |
                Employee.email.ilike(search_pattern) |
                Employee.badge_id.ilike(search_pattern)
            )
        ).offset(skip).limit(limit).all()
    
    def count_by_organization(self, db: Session, *, organization_id: int) -> int:
        """Compter les employés d'une organisation"""
        return db.query(func.count(Employee.id)).filter(
            Employee.organization_id == organization_id
        ).scalar()


# Instance globale
employee = CRUDEmployee(Employee)