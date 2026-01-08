from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.core import security
from app.dependencies import get_current_active_user, get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()

@router.post(
    "/login",
    response_model=schemas.Token,
    summary="Connexion utilisateur",
    description="Authentifie un utilisateur et retourne les tokens JWT ainsi que les informations de l'utilisateur, y compris les rôles et permissions.",
    responses={
        401: {"description": "Email ou mot de passe incorrect"},
    },
)
def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authentifie un utilisateur et retourne un objet Token complet.
    - **username**: L'email de l'utilisateur.
    - **password**: Le mot de passe de l'utilisateur.
    """
    user = security.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Création des tokens
    access_token = security.create_access_token(data={"sub": user.id})
    refresh_token = security.create_refresh_token(data={"sub": user.id})

    # Préparation de la réponse
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
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
        "user": user,
    }

@router.get(
    "/me",
    response_model=schemas.User,
    summary="Obtenir l'utilisateur actuel",
    description="Retourne les informations complètes de l'utilisateur actuellement authentifié.",
)
def read_users_me(current_user: models.user = Depends(get_current_active_user)):
    return current_user


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Déconnexion utilisateur",
    description="Invalide le token d'accès et le refresh token de l'utilisateur. Les tokens sont ajoutés à une blacklist pour empêcher leur réutilisation.",
    responses={
        200: {"description": "Déconnexion réussie"},
        401: {"description": "Token invalide ou manquant"},
    },
)
def logout(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    current_user: models.User = Depends(get_current_active_user),
    refresh_token_data: schemas.RefreshTokenRequest = None,
):
    """
    Déconnecte l'utilisateur en blacklistant son access token et son refresh token.

    - **access_token**: Automatiquement extrait du header Authorization
    - **refresh_token**: Optionnel, à envoyer dans le corps de la requête

    Les deux tokens sont ajoutés à la blacklist pour empêcher leur réutilisation.
    Le frontend doit également supprimer les tokens stockés localement.
    """
    try:
        # Blacklist l'access token
        access_blacklisted = security.blacklist_token(db, token, current_user.id)

        # Blacklist le refresh token si fourni
        refresh_blacklisted = False
        if refresh_token_data and refresh_token_data.refresh_token:
            refresh_blacklisted = security.blacklist_token(
                db,
                refresh_token_data.refresh_token,
                current_user.id
            )

        return {
            "message": "Déconnexion réussie",
            "access_token_revoked": access_blacklisted,
            "refresh_token_revoked": refresh_blacklisted if refresh_token_data else None
        }
    except Exception as e:
        # En cas d'erreur, on retourne quand même un succès
        # car le plus important est que le frontend supprime les tokens
        return {
            "message": "Déconnexion réussie (locale uniquement)",
            "warning": "Les tokens n'ont pas pu être invalidés côté serveur"
        }


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Changer le mot de passe",
    description="Permet à l'utilisateur authentifié de changer son mot de passe en fournissant l'ancien mot de passe.",
    responses={
        200: {"description": "Mot de passe modifié avec succès"},
        400: {"description": "Le nouveau mot de passe doit être différent de l'ancien"},
        401: {"description": "Mot de passe actuel incorrect"},
    },
)
def change_password(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    password_data: schemas.PasswordChange,
):
    """
    Change le mot de passe de l'utilisateur authentifié.

    - **current_password**: Le mot de passe actuel de l'utilisateur
    - **new_password**: Le nouveau mot de passe (minimum 8 caractères)

    Cette méthode est plus sécurisée que la mise à jour via PUT /users/{id}
    car elle vérifie l'ancien mot de passe avant d'autoriser le changement.
    """
    # Vérifier que le mot de passe actuel est correct
    if not security.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mot de passe actuel incorrect"
        )

    # Vérifier que le nouveau mot de passe est différent de l'ancien
    if security.verify_password(password_data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nouveau mot de passe doit être différent de l'ancien"
        )

    # Mettre à jour le mot de passe
    hashed_password = security.get_password_hash(password_data.new_password)
    crud.user.update(db=db, db_obj=current_user, obj_in={"hashed_password": hashed_password})

    return {"message": "Mot de passe modifié avec succès"}