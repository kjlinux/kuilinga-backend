from sqlalchemy.orm import Session, joinedload
from typing import Dict, Any, Optional
from sqlalchemy import or_, asc, desc
from app.crud.base import CRUDBase
from app.models.site import Site
from app.schemas.site import SiteCreate, SiteUpdate

class CRUDSite(CRUDBase[Site, SiteCreate, SiteUpdate]):
    def get_multi_paginated(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "asc"
    ) -> Dict[str, Any]:
        query = db.query(self.model).options(joinedload(Site.organization))

        # Search functionality
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Site.name.ilike(search_filter),
                    Site.address.ilike(search_filter),
                    Site.city.ilike(search_filter),
                    Site.country.ilike(search_filter)
                )
            )

        total = query.count()

        # Sort functionality
        if sort_by:
            valid_columns = ["name", "address", "city", "country", "created_at", "updated_at"]
            if sort_by in valid_columns:
                column = getattr(Site, sort_by)
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
            else:
                query = query.order_by(Site.name)
        else:
            query = query.order_by(Site.name)

        items = query.offset(skip).limit(limit).all()
        return {"items": items, "total": total}

    def create_with_organization(self, db: Session, *, obj_in: SiteCreate) -> Site:
        # This is a placeholder. The actual creation logic is in the base class.
        # We just need to ensure the organization is loaded in the response.
        db_obj = super().create(db, obj_in=obj_in)
        db.refresh(db_obj, ["organization"])
        return db_obj

    def count_by_organization(self, db: Session, *, organization_id: str) -> int:
        return db.query(self.model).filter(Site.organization_id == organization_id).count()

site = CRUDSite(Site)