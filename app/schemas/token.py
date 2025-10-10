from pydantic import BaseModel, Field
from typing import Optional

# Schéma pour la réponse de token standard (login)
class Token(BaseModel):
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    refresh_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field("bearer", example="bearer")

# Schéma pour le payload contenu dans le JWT
class TokenPayload(BaseModel):
    sub: Optional[str] = Field(None, description="Subject (user ID)")
    type: Optional[str] = Field(None, description="Type of token (e.g., access, refresh)")
    # Vous pouvez ajouter d'autres champs comme les rôles, permissions, etc.
    # roles: Optional[list[str]] = []

# Schéma pour la requête de rafraîchissement de token
class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")