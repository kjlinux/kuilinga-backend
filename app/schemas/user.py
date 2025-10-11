from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from app.models.user import UserRole

# Propriétés partagées pour les utilisateurs
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com")
    full_name: Optional[str] = Field(None, example="John Doe")
    phone_number: Optional[str] = Field(None, example="+1234567890")
    role: UserRole = Field(..., example=UserRole.EMPLOYEE)
    organization_id: Optional[str] = Field(None, example="org_a3a2e3a4-5b6c-7d8e-9f0a-1b2c3d4e5f67")

# Propriétés pour la création d'un utilisateur
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="strongpassword123")

# Propriétés pour la mise à jour d'un utilisateur
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, example="johndoe_new@example.com")
    full_name: Optional[str] = Field(None, example="John A. Doe")
    phone_number: Optional[str] = Field(None, example="+1987654321")
    password: Optional[str] = Field(None, min_length=8, example="new_strong_password")
    role: Optional[UserRole] = Field(None, example=UserRole.MANAGER)
    is_active: Optional[bool] = None

# Propriétés à retourner via l'API
class User(UserBase):
    id: str = Field(..., example="user_a3a2e3a4-5b6c-7d8e-9f0a-1b2c3d4e5f67")
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True
