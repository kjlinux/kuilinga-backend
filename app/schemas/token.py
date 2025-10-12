from pydantic import BaseModel, Field
from typing import Optional, List
from .role import Role


# Schéma minimal pour l'utilisateur retourné lors du login
class UserInLogin(BaseModel):
    id: str
    full_name: Optional[str] = None
    email: str
    is_superuser: bool = False
    roles: List[Role] = []

    class Config:
        orm_mode = True


# Schéma pour la réponse de l'endpoint de login
class Token(BaseModel):
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    refresh_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field("bearer", example="bearer")
    user: UserInLogin


# Schéma pour les données contenues dans le JWT (le payload)
class TokenPayload(BaseModel):
    sub: Optional[str] = None


# Schéma pour la requête de rafraîchissement du token
class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
