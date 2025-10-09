from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class Token(BaseModel):
    """Schéma de réponse de token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Payload du token JWT"""
    sub: Optional[UUID] = None  # user_id
    type: Optional[str] = None  # access ou refresh


class RefreshTokenRequest(BaseModel):
    """Requête de rafraîchissement de token"""
    refresh_token: str