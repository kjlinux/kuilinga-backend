from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class Organization(BaseModel):
    """Modèle de données pour les organisations"""
    __tablename__ = "organizations"

    name = Column(String, nullable=False)
    plan = Column(String)
    settings = Column(JSON)

    sites = relationship("Site", back_populates="organization")
    employees = relationship("Employee", back_populates="organization")

class Site(BaseModel):
    """Modèle de données pour les sites"""
    __tablename__ = "sites"

    name = Column(String, nullable=False)
    address = Column(String)
    timezone = Column(String, default="UTC")
    organization_id = Column(ForeignKey("organizations.id"), nullable=False)

    organization = relationship("Organization", back_populates="sites")
    employees = relationship("Employee", back_populates="site")