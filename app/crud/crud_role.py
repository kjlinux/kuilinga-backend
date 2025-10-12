from typing import List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.role import Role, Permission
from app.schemas.role import RoleCreate, RoleUpdate

class CRUDRole(CRUDBase[Role, RoleCreate, RoleUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Role | None:
        return db.query(Role).filter(Role.name == name).first()

    def assign_permissions_to_role(
        self, db: Session, *, role: Role, permissions: List[Permission]
    ) -> Role:
        """
        Assigns a list of permissions to a role.
        """
        role.permissions.extend(permissions)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    def revoke_permission_from_role(
        self, db: Session, *, role: Role, permission: Permission
    ) -> Role:
        """
        Revokes a permission from a role.
        """
        if permission in role.permissions:
            role.permissions.remove(permission)
            db.add(role)
            db.commit()
            db.refresh(role)
        return role

role = CRUDRole(Role)
