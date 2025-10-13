from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from app.models.user import User
from app.models.organization import Organization, Site
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.device import Device
from app.models.department import Department
from app.models.leave import Leave
from app.models.role import Role, Permission
