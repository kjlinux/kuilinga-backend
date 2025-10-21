from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel
from .role import user_roles


class User(BaseModel):
    __tablename__ = "users"

    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    profile_picture_url = Column(String, nullable=True)
    password_reset_token = Column(String, nullable=True)
    password_reset_token_expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)

    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True)

    organization = relationship("Organization", back_populates="users")
    employee = relationship("Employee", back_populates="user", uselist=False)
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    approved_leaves = relationship("Leave", back_populates="approver")
