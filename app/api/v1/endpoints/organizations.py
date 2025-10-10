from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.crud.organization import organization as org_crud
from app.crud.employee import employee as employee_crud
from app.crud.attendance import attendance as attendance_crud
from app.models.device import Device
from app.schemas.organization import (
    Organization, 
    OrganizationCreate, 
    OrganizationUpdate,
    OrganizationList,
    OrganizationStats
)
from app.models.user import User, UserRole
from app.dependencies import get_current_active_user, require_role
from app.models.attendance import AttendanceStatus
from datetime import date, datetime

router = APIRouter()


@router.get("/", response_model=OrganizationList)
def read_organizations(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    is_active: Optional[bool] = None,
    plan: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> OrganizationList:
    """
    Récupérer la liste des organisations (Admin seulement)
    """
    if search:
        organizations = org_crud.search(
            db,
            search_term=search,
            skip=skip,
            limit=limit
        )
    elif plan:
        organizations = org_crud.get_by_plan(
            db,
            plan=plan,
            skip=skip,
            limit=limit
        )
    elif is_active is not None:
        if is_active:
            organizations = org_crud.get_active(db, skip=skip, limit=limit)
        else:
            all_orgs = org_crud.get_multi(db, skip=skip, limit=limit)
            organizations = [o for o in all_orgs if not o.is_active]
    else:
        organizations = org_crud.get_multi(db, skip=skip, limit=limit)
    
    total = org_crud.count(db)
    
    return {
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit,
        "organizations": organizations
    }


@router.get("/{organization_id}", response_model=Organization)
def read_organization(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Organization:
    """
    Récupérer une organisation par ID
    """
    organization = org_crud.get(db, id=organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation non trouvée"
        )
    return organization


@router.get("/{organization_id}/stats", response_model=OrganizationStats)
def read_organization_stats(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MANAGER, UserRole.ADMIN)),
) -> OrganizationStats:
    """
    Récupérer les statistiques d'une organisation
    """
    organization = org_crud.get(db, id=organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation non trouvée"
        )
    
    # Compter les employés
    total_employees = employee_crud.count_by_organization(db, organization_id=organization_id)
    active_employees = len(employee_crud.get_by_organization(
        db, organization_id=organization_id, is_active=True, limit=10000
    ))
    inactive_employees = total_employees - active_employees
    
    # Compter les devices
    total_devices = db.query(func.count(Device.id)).filter(
        Device.organization_id == organization_id
    ).scalar()
    
    active_devices = db.query(func.count(Device.id)).filter(
        Device.organization_id == organization_id,
        Device.is_online == True
    ).scalar()
    
    # Pointages du jour
    today_attendances = attendance_crud.get_today_attendances(
        db,
        organization_id=organization_id
    )
    
    # Compter les présents
    present_today = attendance_crud.count_by_status(
        db,
        organization_id=organization_id,
        status=AttendanceStatus.PRESENT,
        target_date=date.today()
    )
    
    # Taux de présence
    attendance_rate = (present_today / total_employees * 100) if total_employees > 0 else 0
    
    return {
        "organization_id": organization.id,
        "organization_name": organization.name,
        "total_employees": total_employees,
        "active_employees": active_employees,
        "inactive_employees": inactive_employees,
        "total_devices": total_devices or 0,
        "active_devices": active_devices or 0,
        "total_attendances_today": len(today_attendances),
        "attendance_rate_today": round(attendance_rate, 2)
    }


@router.post("/", response_model=Organization, status_code=status.HTTP_201_CREATED)
def create_organization(
    *,
    db: Session = Depends(get_db),
    organization_in: OrganizationCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> Organization:
    """
    Créer une nouvelle organisation (Admin seulement)
    """
    # Vérifier si le nom existe déjà
    existing_org = org_crud.get_by_name(db, name=organization_in.name)
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Une organisation avec ce nom existe déjà"
        )
    
    organization = org_crud.create(db, obj_in=organization_in)
    return organization


@router.put("/{organization_id}", response_model=Organization)
def update_organization(
    *,
    db: Session = Depends(get_db),
    organization_id: UUID,
    organization_in: OrganizationUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> Organization:
    """
    Mettre à jour une organisation (Admin seulement)
    """
    organization = org_crud.get(db, id=organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation non trouvée"
        )
    
    organization = org_crud.update(db, db_obj=organization, obj_in=organization_in)
    return organization


@router.post("/{organization_id}/activate", response_model=Organization)
def activate_organization(
    *,
    db: Session = Depends(get_db),
    organization_id: UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> Organization:
    """
    Activer une organisation
    """
    organization = org_crud.activate(db, organization_id=organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation non trouvée"
        )
    return organization


@router.post("/{organization_id}/deactivate", response_model=Organization)
def deactivate_organization(
    *,
    db: Session = Depends(get_db),
    organization_id: UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> Organization:
    """
    Désactiver une organisation
    """
    organization = org_crud.deactivate(db, organization_id=organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation non trouvée"
        )
    return organization


@router.delete("/{organization_id}", response_model=Organization)
def delete_organization(
    *,
    db: Session = Depends(get_db),
    organization_id: UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> Organization:
    """
    Supprimer une organisation (Admin seulement)
    """
    organization = org_crud.get(db, id=organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation non trouvée"
        )
    
    # Vérifier s'il y a des employés
    emp_count = employee_crud.count_by_organization(db, organization_id=organization_id)
    if emp_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de supprimer: {emp_count} employé(s) associé(s)"
        )
    
    organization = org_crud.delete(db, id=organization_id)
    return organization