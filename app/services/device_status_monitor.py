"""
Service de surveillance du statut des terminaux IoT.

Ce service s'exécute en arrière-plan pour détecter automatiquement
les terminaux qui n'ont pas envoyé de heartbeat depuis un certain temps
et les marquer comme OFFLINE.
"""
import asyncio
import logging
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.crud.device import device as crud_device
from app.config import settings

logger = logging.getLogger(__name__)


class DeviceStatusMonitorService:
    """
    Service qui surveille périodiquement les heartbeats des terminaux
    et marque OFFLINE ceux qui n'ont pas communiqué récemment.
    """

    def __init__(
        self,
        check_interval_seconds: int = 60,
        offline_timeout_minutes: int = 5
    ):
        """
        Initialise le service de surveillance.

        Args:
            check_interval_seconds: Intervalle entre chaque vérification (en secondes)
            offline_timeout_minutes: Temps sans heartbeat avant de marquer OFFLINE (en minutes)
        """
        self.check_interval_seconds = check_interval_seconds
        self.offline_timeout_minutes = offline_timeout_minutes
        self.is_running = False
        self.task = None

    async def check_device_status(self) -> int:
        """
        Vérifie les devices et marque OFFLINE ceux sans heartbeat récent.

        Returns:
            Le nombre de devices marqués OFFLINE
        """
        try:
            db = SessionLocal()
            marked_offline = crud_device.mark_devices_offline(
                db,
                timeout_minutes=self.offline_timeout_minutes
            )
            db.close()

            if marked_offline > 0:
                logger.info(
                    f"Device status check: {marked_offline} device(s) marked OFFLINE "
                    f"(no heartbeat for {self.offline_timeout_minutes} min)"
                )
            else:
                logger.debug("Device status check: All devices up to date")

            return marked_offline

        except Exception as e:
            logger.error(f"Error during device status check: {str(e)}")
            return 0

    async def _monitor_loop(self):
        """
        Boucle de surveillance qui s'exécute à intervalle régulier.
        """
        logger.info(
            f"Device status monitor started "
            f"(check interval: {self.check_interval_seconds}s, "
            f"offline timeout: {self.offline_timeout_minutes}min)"
        )

        while self.is_running:
            try:
                await self.check_device_status()
            except Exception as e:
                logger.error(f"Error in monitor loop: {str(e)}")

            # Attendre jusqu'à la prochaine vérification
            await asyncio.sleep(self.check_interval_seconds)

    def start(self):
        """
        Démarre le service de surveillance.
        """
        if self.is_running:
            logger.warning("Device status monitor is already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._monitor_loop())
        logger.info("Device status monitor started")

    async def stop(self):
        """
        Arrête le service de surveillance.
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

        logger.info("Device status monitor stopped")

    async def manual_check(self) -> int:
        """
        Déclenche une vérification manuelle immédiate.

        Returns:
            Le nombre de devices marqués OFFLINE
        """
        logger.info("Manual device status check triggered")
        return await self.check_device_status()

    def get_status(self) -> dict:
        """
        Retourne le statut actuel du service.
        """
        return {
            "is_running": self.is_running,
            "check_interval_seconds": self.check_interval_seconds,
            "offline_timeout_minutes": self.offline_timeout_minutes
        }


# Récupérer les paramètres depuis les settings si disponibles
_check_interval = getattr(settings, 'DEVICE_STATUS_CHECK_INTERVAL_SECONDS', 60)
_offline_timeout = getattr(settings, 'DEVICE_OFFLINE_TIMEOUT_MINUTES', 5)

# Instance globale du service de surveillance
device_status_monitor = DeviceStatusMonitorService(
    check_interval_seconds=_check_interval,
    offline_timeout_minutes=_offline_timeout
)
