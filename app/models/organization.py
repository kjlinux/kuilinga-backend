from sqlalchemy import Column, String, Boolean, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel
from .site import Site

class Organization(BaseModel):
    __tablename__ = "organizations"

    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, nullable=True)
    timezone = Column(String, default="UTC")
    plan = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, nullable=True)

    users = relationship("User", back_populates="organization")
    sites = relationship("Site", back_populates="organization", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="organization", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="organization", cascade="all, delete-orphan")