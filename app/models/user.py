import enum
from sqlalchemy import Column, String, Enum, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class UserRole(str, enum.Enum):
    """Énumération pour les rôles utilisateur"""
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    INTEGRATOR = "integrator"

class User(BaseModel):
    """Modèle de données pour les utilisateurs"""
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    employee = relationship("Employee", back_populates="user", uselist=False)