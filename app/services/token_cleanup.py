"""
Service de nettoyage des tokens blacklistés expirés.
Ce service s'exécute en arrière-plan pour supprimer périodiquement
les tokens expirés de la base de données.
"""
import asyncio
import logging
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.crud.blacklisted_token import blacklisted_token

logger = logging.getLogger(__name__)


class TokenCleanupService:
    """
    Service qui nettoie périodiquement les tokens blacklistés expirés.
    """

    def __init__(self, interval_hours: int = 24):
        """
        Initialise le service de nettoyage.

        Args:
            interval_hours: Intervalle entre chaque nettoyage (en heures)
        """
        self.interval_hours = interval_hours
        self.is_running = False
        self.task = None

    async def cleanup_expired_tokens(self):
        """
        Supprime les tokens expirés de la blacklist.
        """
        try:
            db = SessionLocal()
            deleted_count = blacklisted_token.remove_expired(db)
            db.close()

            if deleted_count > 0:
                logger.info(
                    f"Token cleanup: {deleted_count} expired tokens removed from blacklist"
                )
            else:
                logger.debug("Token cleanup: No expired tokens to remove")

            return deleted_count
        except Exception as e:
            logger.error(f"Error during token cleanup: {str(e)}")
            return 0

    async def _cleanup_loop(self):
        """
        Boucle de nettoyage qui s'exécute à intervalle régulier.
        """
        logger.info(
            f"Token cleanup service started (interval: {self.interval_hours}h)"
        )

        while self.is_running:
            try:
                await self.cleanup_expired_tokens()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")

            # Attendre jusqu'au prochain nettoyage
            await asyncio.sleep(self.interval_hours * 3600)

    def start(self):
        """
        Démarre le service de nettoyage.
        """
        if self.is_running:
            logger.warning("Token cleanup service is already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._cleanup_loop())
        logger.info("Token cleanup service started")

    async def stop(self):
        """
        Arrête le service de nettoyage.
        """
        if not self.is_running:
            return

        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("Token cleanup service stopped")

    async def manual_cleanup(self) -> int:
        """
        Déclenche un nettoyage manuel immédiat.

        Returns:
            Le nombre de tokens supprimés
        """
        logger.info("Manual token cleanup triggered")
        return await self.cleanup_expired_tokens()


# Instance globale du service de nettoyage
token_cleanup_service = TokenCleanupService(interval_hours=24)
