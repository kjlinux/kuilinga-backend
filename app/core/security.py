from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import crud, models
from app.config import settings
from app.crud.blacklisted_token import blacklisted_token

# Configuration du hashing de mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe correspond au hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash un mot de passe"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token JWT d'accès
    
    Args:
        data: Données à encoder dans le token
        expires_delta: Durée de validité du token
    
    Returns:
        Token JWT encodé
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Crée un refresh token JWT
    
    Args:
        data: Données à encoder dans le token
    
    Returns:
        Refresh token JWT encodé
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str, db: Optional[Session] = None) -> dict:
    """
    Décode et vérifie un token JWT

    Args:
        token: Token JWT à décoder
        db: Session de la base de données (optionnel, pour vérifier la blacklist)

    Returns:
        Payload du token décodé

    Raises:
        JWTError: Si le token est invalide ou blacklisté
    """
    try:
        # Vérifier si le token est blacklisté (si db session est fournie)
        if db and blacklisted_token.is_blacklisted(db, token):
            raise JWTError("Token has been revoked")

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise JWTError("Token invalide ou expiré")


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """
    Authentifie un utilisateur.

    Args:
        db: Session de la base de données.
        email: Email de l'utilisateur.
        password: Mot de passe de l'utilisateur.

    Returns:
        L'objet utilisateur si l'authentification réussit, sinon None.
    """
    user = crud.user.get_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_from_refresh_token(db: Session, token: str) -> Optional[models.User]:
    """
    Récupère un utilisateur à partir d'un refresh token.

    Args:
        db: Session de la base de données.
        token: Refresh token JWT.

    Returns:
        L'objet utilisateur si le token est valide, sinon None.
    """
    try:
        payload = decode_token(token, db)

        # Vérifier que c'est bien un refresh token
        if payload.get("type") != "refresh":
            return None

        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        user = crud.user.get(db, id=user_id)
        return user
    except JWTError:
        return None


def blacklist_token(db: Session, token: str, user_id: Optional[str] = None) -> bool:
    """
    Ajoute un token à la blacklist.

    Args:
        db: Session de la base de données
        token: Le token JWT à blacklister
        user_id: ID de l'utilisateur (optionnel)

    Returns:
        True si le token a été blacklisté avec succès, False sinon
    """
    try:
        # Décoder le token pour obtenir sa date d'expiration
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = payload.get("exp")

        if exp is None:
            return False

        # Convertir le timestamp en datetime
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)

        # Ajouter à la blacklist
        blacklisted_token.create(
            db,
            token=token,
            expires_at=expires_at,
            user_id=user_id
        )
        return True
    except (JWTError, Exception):
        return False