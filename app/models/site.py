from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class Site(BaseModel):
    __tablename__ = "sites"

    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    timezone = Column(String, default="UTC")

    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)

    organization = relationship("Organization", back_populates="sites")
    employees = relationship("Employee", back_populates="site")
    departments = relationship("Department", back_populates="site", cascade="all, delete-orphan")
