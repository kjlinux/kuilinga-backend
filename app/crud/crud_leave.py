from app.crud.base import CRUDBase
from app.models.leave import Leave
from app.schemas.leave import LeaveCreate, LeaveUpdate

class CRUDLeave(CRUDBase[Leave, LeaveCreate, LeaveUpdate]):
    pass

leave = CRUDLeave(Leave)
