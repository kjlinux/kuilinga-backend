from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class Employee(BaseModel):
    __tablename__ = "employees"

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    employee_number = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    department = Column(String, nullable=True)
    position = Column(String, nullable=True)
    badge_id = Column(String, unique=True, index=True, nullable=True)
    metadata = Column(JSON, nullable=True)

    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    site_id = Column(String, ForeignKey("sites.id"), nullable=True)

    user = relationship("User", back_populates="employee")
    organization = relationship("Organization", back_populates="employees")
    site = relationship("Site", back_populates="employees")
    attendances = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")