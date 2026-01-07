from pydantic import BaseModel, Field
from typing import Optional, List
from .role import Role


# Schéma minimal pour l'utilisateur retourné lors du login
class UserInLogin(BaseModel):
    id: str = Field(..., description="Identifiant unique de l'utilisateur")
    full_name: Optional[str] = Field(None, description="Nom complet de l'utilisateur")
    email: str = Field(..., description="Adresse email de l'utilisateur")
    is_superuser: bool = Field(False, description="Indique si l'utilisateur a tous les droits")
    roles: List[Role] = Field([], description="Liste des rôles attribués à l'utilisateur")

    class Config:
        from_attributes = True


# Schéma pour la réponse de l'endpoint de login
class Token(BaseModel):
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", description="Token JWT pour l'authentification (expire en 30 min)")
    refresh_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", description="Token pour renouveler l'access_token (expire en 7 jours)")
    token_type: str = Field("bearer", example="bearer", description="Type de token (toujours 'bearer')")
    user: UserInLogin = Field(..., description="Informations de l'utilisateur connecté")


# Schéma pour les données contenues dans le JWT (le payload)
class TokenPayload(BaseModel):
    sub: Optional[str] = Field(None, description="Identifiant du sujet (user_id)")


# Schéma pour la requête de rafraîchissement du token
class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", description="Token de rafraîchissement à utiliser")
