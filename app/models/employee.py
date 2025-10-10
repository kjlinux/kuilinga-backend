from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class Employee(BaseModel):
    """Modèle de données pour les employés"""
    __tablename__ = "employees"

    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    badge_id = Column(String, unique=True, index=True)
    metadata = Column(JSON)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True)

    user = relationship("User", back_populates="employee")
    organization = relationship("Organization", back_populates="employees")
    site = relationship("Site", back_populates="employees")
    attendances = relationship("Attendance", back_populates="employee")