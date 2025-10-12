from app.crud.base import CRUDBase
from app.models.role import Permission
from app.schemas.role import PermissionCreate, PermissionUpdate
from sqlalchemy.orm import Session

class CRUDPermission(CRUDBase[Permission, PermissionCreate, PermissionUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Permission | None:
        return db.query(Permission).filter(Permission.name == name).first()

permission = CRUDPermission(Permission)
