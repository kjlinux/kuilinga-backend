from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.blacklisted_token import BlacklistedToken


class CRUDBlacklistedToken:
    """CRUD operations for BlacklistedToken model"""

    def create(
        self,
        db: Session,
        *,
        token: str,
        expires_at: datetime,
        user_id: Optional[str] = None
    ) -> BlacklistedToken:
        """
        Ajoute un token à la blacklist.

        Args:
            db: Session de la base de données
            token: Le token JWT à blacklister
            expires_at: Date d'expiration du token
            user_id: ID de l'utilisateur (optionnel)

        Returns:
            L'objet BlacklistedToken créé
        """
        db_obj = BlacklistedToken(
            token=token,
            expires_at=expires_at,
            user_id=user_id,
            blacklisted_on=datetime.now(timezone.utc)
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def is_blacklisted(self, db: Session, token: str) -> bool:
        """
        Vérifie si un token est blacklisté.

        Args:
            db: Session de la base de données
            token: Le token JWT à vérifier

        Returns:
            True si le token est blacklisté, False sinon
        """
        blacklisted = db.query(BlacklistedToken).filter(
            BlacklistedToken.token == token
        ).first()
        return blacklisted is not None

    def remove_expired(self, db: Session) -> int:
        """
        Supprime tous les tokens expirés de la blacklist.
        Cette opération devrait être exécutée périodiquement pour nettoyer la base.

        Args:
            db: Session de la base de données

        Returns:
            Le nombre de tokens supprimés
        """
        now = datetime.now(timezone.utc)
        deleted_count = db.query(BlacklistedToken).filter(
            BlacklistedToken.expires_at < now
        ).delete()
        db.commit()
        return deleted_count

    def get_blacklist_count(self, db: Session) -> int:
        """
        Retourne le nombre total de tokens dans la blacklist.

        Args:
            db: Session de la base de données

        Returns:
            Le nombre de tokens blacklistés
        """
        return db.query(BlacklistedToken).count()


blacklisted_token = CRUDBlacklistedToken()
