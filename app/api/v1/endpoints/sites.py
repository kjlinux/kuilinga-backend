from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Any
from app import crud, models, schemas
from app.dependencies import get_db, PermissionChecker

router = APIRouter()

def enrich_site_response(db: Session, site: models.Site) -> schemas.Site:
    """
    Enrich the site object with organization details and calculated counts.
    """
    site_schema = schemas.Site.from_orm(site)

    # Get counts
    site_schema.departments_count = crud.department.count_by_site(db, site_id=site.id)
    site_schema.employees_count = crud.employee.count_by_site(db, site_id=site.id)
    site_schema.devices_count = crud.device.count_by_site(db, site_id=site.id)

    return site_schema

@router.post(
    "/",
    response_model=schemas.Site,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker(["site:create"]))],
)
def create_site(
    *,
    db: Session = Depends(get_db),
    site_in: schemas.SiteCreate,
):
    site = crud.site.create_with_organization(db=db, obj_in=site_in)
    return enrich_site_response(db, site)

@router.get(
    "/",
    response_model=schemas.PaginatedResponse[schemas.Site],
    dependencies=[Depends(PermissionChecker(["site:read"]))],
)
def read_sites(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Nombre de sites à sauter"),
    limit: int = Query(100, description="Nombre maximum de sites à retourner"),
    search: str = Query(None, description="Recherche textuelle (nom, adresse, ville, pays)"),
    sort_by: str = Query(None, description="Champ de tri (name, address, city, country, created_at, updated_at)"),
    sort_order: str = Query("asc", description="Direction du tri (asc ou desc)"),
) -> Any:
    site_data = crud.site.get_multi_paginated(
        db,
        skip=skip,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

    enriched_items = [enrich_site_response(db, site) for site in site_data["items"]]

    return {
        "items": enriched_items,
        "total": site_data["total"],
        "skip": skip,
        "limit": limit,
    }

@router.get(
    "/{site_id}",
    response_model=schemas.Site,
    dependencies=[Depends(PermissionChecker(["site:read"]))],
)
def read_site(
    *,
    db: Session = Depends(get_db),
    site_id: str,
):
    site = crud.site.get(db=db, id=site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return enrich_site_response(db, site)

@router.put(
    "/{site_id}",
    response_model=schemas.Site,
    dependencies=[Depends(PermissionChecker(["site:update"]))],
)
def update_site(
    *,
    db: Session = Depends(get_db),
    site_id: str,
    site_in: schemas.SiteUpdate,
):
    site = crud.site.get(db=db, id=site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    site = crud.site.update(db=db, db_obj=site, obj_in=site_in)
    return enrich_site_response(db, site)

@router.delete(
    "/{site_id}",
    response_model=schemas.Site,
    dependencies=[Depends(PermissionChecker(["site:delete"]))],
)
def delete_site(
    *,
    db: Session = Depends(get_db),
    site_id: str,
):
    site = crud.site.get(db=db, id=site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    # Build response data while session is still active
    response_data = enrich_site_response(db, site)
    crud.site.remove(db=db, id=site_id)
    return response_data