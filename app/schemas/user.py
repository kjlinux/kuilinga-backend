from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from app.models.user import UserRole
from typing import Optional

# Schéma de base pour les propriétés communes
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com")
    role: UserRole = Field(..., example=UserRole.EMPLOYEE)

    class Config:
        from_attributes = True

# Schéma pour la création d'un utilisateur (avec mot de passe)
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="strongpassword123")

# Schéma pour la mise à jour d'un utilisateur (champs optionnels)
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, example="johndoe_new@example.com")
    role: Optional[UserRole] = Field(None, example=UserRole.MANAGER)
    password: Optional[str] = Field(None, min_length=8, example="new_strong_password")
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

# Schéma pour la lecture des données d'un utilisateur (sans mot de passe)
class User(UserBase):
    id: UUID = Field(..., example="a3a2e3a4-5b6c-7d8e-9f0a-1b2c3d4e5f67")
    is_active: bool
    is_superuser: bool