from typing import Any, Dict, Optional, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, asc, desc
from app.crud.base import CRUDBase
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(self.model).filter(User.email == email).first()

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
        query = db.query(self.model).options(
            joinedload(User.organization),
            joinedload(User.roles),
            joinedload(User.employee)
        )

        # Search functionality
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_filter),
                    User.full_name.ilike(search_filter)
                )
            )

        total = query.count()

        # Sort functionality
        if sort_by:
            valid_columns = ["email", "full_name", "created_at", "updated_at"]
            if sort_by in valid_columns:
                column = getattr(User, sort_by)
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
            else:
                query = query.order_by(User.email)
        else:
            query = query.order_by(User.email)

        items = query.offset(skip).limit(limit).all()
        return {"items": items, "total": total}

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        from app.core.security import get_password_hash
        create_data = obj_in.model_dump()
        create_data.pop("password")
        db_obj = self.model(**create_data)
        db_obj.hashed_password = get_password_hash(obj_in.password)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        from app.core.security import get_password_hash
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password

        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser

    def assign_role(self, db: Session, *, user: User, role: Role) -> User:
        user.roles.append(role)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def count_by_organization(self, db: Session, *, organization_id: str) -> int:
        return db.query(self.model).filter(User.organization_id == organization_id).count()

user = CRUDUser(User)
