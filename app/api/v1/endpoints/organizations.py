from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.dependencies import get_db, get_current_active_user, require_role

router = APIRouter()

def enrich_organization_response(db: Session, org: models.Organization) -> schemas.Organization:
    """
    Enrich the organization object with calculated counts.
    """
    # Convert SQLAlchemy model to Pydantic model
    org_schema = schemas.Organization.from_orm(org)

    # Calculate counts
    org_schema.sites_count = crud.site.count_by_organization(db, organization_id=org.id)
    org_schema.employees_count = crud.employee.count_by_organization(db, organization_id=org.id)
    org_schema.users_count = crud.user.count_by_organization(db, organization_id=org.id)

    return org_schema

@router.get(
    "/",
    response_model=schemas.PaginatedResponse[schemas.Organization],
    summary="Lister toutes les organisations",
    description="Récupère une liste paginée de toutes les organisations. **Requiert le rôle 'admin'.**",
)
def read_organizations(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Nombre d'organisations à sauter"),
    limit: int = Query(100, description="Nombre maximum d'organisations à retourner"),
    current_user: models.User = Depends(require_role("admin")),
) -> Any:
    organization_data = crud.organization.get_multi(db, skip=skip, limit=limit)

    enriched_items = [enrich_organization_response(db, org) for org in organization_data["items"]]

    return {
        "items": enriched_items,
        "total": organization_data["total"],
        "skip": skip,
        "limit": limit,
    }

@router.post(
    "/",
    response_model=schemas.Organization,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une nouvelle organisation",
    description="Crée une nouvelle organisation. **Requiert le rôle 'admin'.**",
)
def create_organization(
    *,
    db: Session = Depends(get_db),
    organization_in: schemas.OrganizationCreate,
    current_user: models.User = Depends(require_role("admin")),
) -> Any:
    organization = crud.organization.create(db=db, obj_in=organization_in)
    return enrich_organization_response(db, organization)

@router.get(
    "/{org_id}",
    response_model=schemas.Organization,
    summary="Lire une organisation par ID",
    description="Récupère les informations d'une organisation par son ID. Un utilisateur normal ne peut voir que son organisation.",
    responses={
        403: {"description": "Permissions insuffisantes"},
        404: {"description": "Organisation non trouvée"},
    },
)
def read_organization(
    *,
    db: Session = Depends(get_db),
    org_id: str,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    organization = crud.organization.get(db=db, id=org_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation non trouvée")
    
    if not current_user.is_superuser and current_user.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")

    return enrich_organization_response(db, organization)

@router.put(
    "/{org_id}",
    response_model=schemas.Organization,
    summary="Mettre à jour une organisation",
    description="Met à jour les informations d'une organisation. **Requiert le rôle 'admin'.**",
    responses={
        404: {"description": "Organisation non trouvée"},
    },
)
def update_organization(
    *,
    db: Session = Depends(get_db),
    org_id: str,
    organization_in: schemas.OrganizationUpdate,
    current_user: models.User = Depends(require_role("admin")),
) -> Any:
    organization = crud.organization.get(db=db, id=org_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation non trouvée")

    organization = crud.organization.update(db=db, db_obj=organization, obj_in=organization_in)
    return enrich_organization_response(db, organization)

@router.delete(
    "/{org_id}",
    response_model=schemas.Organization,
    summary="Supprimer une organisation",
    description="Supprime une organisation. **Requiert le rôle 'admin'.**",
    responses={
        404: {"description": "Organisation non trouvée"},
    },
)
def delete_organization(
    *,
    db: Session = Depends(get_db),
    org_id: str,
    current_user: models.User = Depends(require_role("admin")),
) -> Any:
    organization = crud.organization.get(db=db, id=org_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation non trouvée")

    deleted_organization = crud.organization.remove(db=db, id=org_id)
    return enrich_organization_response(db, deleted_organization)