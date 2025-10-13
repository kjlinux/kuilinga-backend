from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel
from .leave import Leave


class Employee(BaseModel):
    __tablename__ = "employees"

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    employee_number = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    position = Column(String, nullable=True)
    badge_id = Column(String, unique=True, index=True, nullable=True)
    extra_data = Column(JSON, nullable=True)

    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    site_id = Column(String, ForeignKey("sites.id"), nullable=True)
    department_id = Column(String, ForeignKey("departments.id"), nullable=True)

    user = relationship("User", back_populates="employee")
    organization = relationship("Organization", back_populates="employees")
    site = relationship("Site", back_populates="employees")
    department = relationship(
        "Department",
        back_populates="employees",
        foreign_keys=[department_id],
    )
    attendances = relationship(
        "Attendance", back_populates="employee", cascade="all, delete-orphan"
    )
    leaves = relationship("Leave", back_populates="employee", cascade="all, delete-orphan")