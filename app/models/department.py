from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class Department(BaseModel):
    __tablename__ = "departments"

    name = Column(String, index=True, nullable=False)

    site_id = Column(String, ForeignKey("sites.id"), nullable=False)
    manager_id = Column(String, ForeignKey("employees.id"), nullable=True)

    site = relationship("Site", back_populates="departments")
    manager = relationship("Employee", foreign_keys=[manager_id])
    employees = relationship(
        "Employee",
        back_populates="department",
        foreign_keys="[Employee.department_id]",
    )
