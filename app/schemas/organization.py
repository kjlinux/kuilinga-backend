from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class OrganizationBase(BaseModel):
    """Schéma de base organisation"""
    name: str
    description: Optional[str] = None
    plan: str = "free"  # free, basic, premium
    timezone: str = "Africa/Abidjan"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    settings: Optional[Dict[str, Any]] = {}


class OrganizationCreate(OrganizationBase):
    """Schéma de création d'organisation"""
    pass


class OrganizationUpdate(BaseModel):
    """Schéma de mise à jour d'organisation"""
    name: Optional[str] = None
    description: Optional[str] = None
    plan: Optional[str] = None
    timezone: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class Organization(OrganizationBase):
    """Schéma de réponse organisation"""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OrganizationList(BaseModel):
    """Liste paginée d'organisations"""
    total: int
    page: int
    page_size: int
    organizations: list[Organization]


class OrganizationStats(BaseModel):
    """Statistiques d'une organisation"""
    organization_id: UUID
    organization_name: str
    total_employees: int
    active_employees: int
    inactive_employees: int
    total_devices: int
    active_devices: int
    total_attendances_today: int
    attendance_rate_today: float