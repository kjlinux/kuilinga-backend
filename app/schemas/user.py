from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from .role import Role # Importer le nouveau schéma de rôle

# Propriétés partagées pour les utilisateurs
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com", description="Adresse email (identifiant de connexion)")
    full_name: Optional[str] = Field(None, example="John Doe", description="Nom complet de l'utilisateur")
    phone_number: Optional[str] = Field(None, example="+1234567890", description="Numéro de téléphone")
    organization_id: Optional[str] = Field(None, example="org_a3a2e3a4-5b6c-7d8e-9f0a-1b2c3d4e5f67", description="ID de l'organisation d'appartenance")

# Propriétés pour la création d'un utilisateur
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, example="strongpassword123", description="Mot de passe (minimum 8 caractères)")

# Propriétés pour la mise à jour d'un utilisateur
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, example="johndoe_new@example.com", description="Adresse email")
    full_name: Optional[str] = Field(None, example="John A. Doe", description="Nom complet de l'utilisateur")
    phone_number: Optional[str] = Field(None, example="+1987654321", description="Numéro de téléphone")
    password: Optional[str] = Field(None, min_length=8, example="new_strong_password", description="Nouveau mot de passe")
    is_active: Optional[bool] = Field(None, description="Indique si le compte est actif")

# Propriétés à retourner via l'API (inclut maintenant les rôles)
class User(UserBase):
    id: str = Field(..., example="user_a3a2e3a4-5b6c-7d8e-9f0a-1b2c3d4e5f67", description="Identifiant unique de l'utilisateur")
    is_active: bool = Field(..., description="Indique si le compte est actif")
    is_superuser: bool = Field(..., description="Indique si l'utilisateur a tous les droits")
    avatar_url: Optional[str] = Field(None, description="URL de la photo de profil")
    roles: List[Role] = Field([], description="Liste des rôles attribués à l'utilisateur")

    class Config:
        from_attributes = True


# Schéma pour le changement de mot de passe sécurisé
class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=1, description="Mot de passe actuel")
    new_password: str = Field(..., min_length=8, description="Nouveau mot de passe (minimum 8 caractères)")


# Schéma pour la réponse d'upload d'avatar
class AvatarUploadResponse(BaseModel):
    avatar_url: str = Field(..., description="URL de la photo de profil uploadée")
    message: str = Field(default="Avatar uploadé avec succès")
