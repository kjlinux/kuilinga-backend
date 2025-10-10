from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import models, schemas
from app.core import security
from app.dependencies import get_current_active_user, get_db

router = APIRouter()

@router.post(
    "/login",
    response_model=schemas.Token,
    summary="Connexion utilisateur",
    description="Authentifie un utilisateur avec email et mot de passe, puis retourne un JWT.",
    responses={
        401: {"description": "Email ou mot de passe incorrect"},
    },
)
def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = security.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(data={"sub": user.id})
    refresh_token = security.create_refresh_token(data={"sub": user.id})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post(
    "/refresh",
    response_model=schemas.Token,
    summary="Rafraîchir le token d'accès",
    description="Génère un nouveau token d'accès en utilisant un refresh token valide.",
    responses={
        401: {"description": "Refresh token invalide ou expiré"},
    },
)
def refresh_access_token(
    refresh_token: schemas.RefreshTokenRequest, db: Session = Depends(get_db)
):
    user = security.get_user_from_refresh_token(db, token=refresh_token.refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expiré",
        )
    access_token = security.create_access_token(data={"sub": user.id})
    new_refresh_token = security.create_refresh_token(data={"sub": user.id})
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }

@router.get(
    "/me",
    response_model=schemas.User,
    summary="Obtenir l'utilisateur actuel",
    description="Retourne les informations complètes de l'utilisateur actuellement authentifié.",
)
def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user