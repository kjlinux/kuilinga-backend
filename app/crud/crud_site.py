from sqlalchemy.orm import Session, joinedload
from typing import Dict, Any
from app.crud.base import CRUDBase
from app.models.site import Site
from app.schemas.site import SiteCreate, SiteUpdate

class CRUDSite(CRUDBase[Site, SiteCreate, SiteUpdate]):
    def get_multi_paginated(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> Dict[str, Any]:
        query = db.query(self.model).options(joinedload(Site.organization))
        total = query.count()
        items = query.order_by(Site.name).offset(skip).limit(limit).all()
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