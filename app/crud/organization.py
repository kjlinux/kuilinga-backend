from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc
from app.crud.base import CRUDBase
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate

class CRUDOrganization(CRUDBase[Organization, OrganizationCreate, OrganizationUpdate]):
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
        query = db.query(self.model)

        # Search functionality
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Organization.name.ilike(search_filter),
                    Organization.address.ilike(search_filter),
                    Organization.contact_email.ilike(search_filter),
                    Organization.contact_phone.ilike(search_filter)
                )
            )

        total = query.count()

        # Sort functionality
        if sort_by:
            valid_columns = ["name", "address", "contact_email", "contact_phone", "created_at", "updated_at"]
            if sort_by in valid_columns:
                column = getattr(Organization, sort_by)
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
            else:
                query = query.order_by(Organization.name)
        else:
            query = query.order_by(Organization.name)

        items = query.offset(skip).limit(limit).all()
        return {"items": items, "total": total}

organization = CRUDOrganization(Organization)