from typing import Any, Dict, Optional, Union
from sqlalchemy.orm import Session
import secrets
from datetime import datetime, timedelta
from app.crud.base import CRUDBase
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(self.model).filter(User.email == email).first()

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

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100, include_inactive: bool = False
    ) -> Dict[str, Any]:
        query = db.query(self.model)
        if not include_inactive:
            query = query.filter(User.is_active == True)

        total = query.count()
        items = query.order_by(self.model.id).offset(skip).limit(limit).all()
        return {"items": items, "total": total}

    def set_password_reset_token(self, db: Session, *, user: User) -> str:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        user.password_reset_token = token
        user.password_reset_token_expires_at = expires_at
        db.add(user)
        db.commit()
        db.refresh(user)
        return token

user = CRUDUser(User)
