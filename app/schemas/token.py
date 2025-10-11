from pydantic import BaseModel, Field
from typing import Optional

# Schéma pour le token JWT
class Token(BaseModel):
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    refresh_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field("bearer", example="bearer")

# Schéma pour les données contenues dans le token
class TokenPayload(BaseModel):
    sub: Optional[str] = None

# Schéma pour la requête de rafraîchissement du token
class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
