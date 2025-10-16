from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, models, schemas
from app.dependencies import get_db, PermissionChecker

router = APIRouter()

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
    """
    Create a new site. Requires permission: `site:create`.
    """
    site = crud.site.create(db=db, obj_in=site_in)
    return site

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any
from app import crud, models, schemas
from app.dependencies import get_db, PermissionChecker

@router.get(
    "/",
    response_model=schemas.PaginatedResponse[schemas.Site],
    dependencies=[Depends(PermissionChecker(["site:read"]))],
)
def read_sites(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Nombre de sites à sauter"),
    limit: int = Query(100, description="Nombre maximum de sites à retourner"),
) -> Any:
    """
    Retrieve sites. Requires permission: `site:read`.
    """
    site_data = crud.site.get_multi(db, skip=skip, limit=limit)
    return {
        "items": site_data["items"],
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
    """
    Get site by ID. Requires permission: `site:read`.
    """
    site = crud.site.get(db=db, id=site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site

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
    """
    Update a site. Requires permission: `site:update`.
    """
    site = crud.site.get(db=db, id=site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    site = crud.site.update(db=db, db_obj=site, obj_in=site_in)
    return site

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
    """
    Delete a site. Requires permission: `site:delete`.
    """
    site = crud.site.get(db=db, id=site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    site = crud.site.remove(db=db, id=site_id)
    return site
