"""
Client MQTT pour la communication avec les appareils IoT.

Fonctionnalités:
- Connexion sécurisée via SSL/TLS avec certificats
- Réception des pointages depuis les badges
- Envoi des réponses de validation (ACCEPTED/REFUSED/REJECTED)
- Envoi des commandes administratives (RESET/REBOOT/SLEEP/STATUS)
"""
import json
import logging
import asyncio
import ssl
from datetime import datetime
from pathlib import Path
from typing import Optional

import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

from app.config import settings
from app.crud.attendance import attendance as crud_attendance
from app.crud.employee import employee as crud_employee
from app.crud.device import device as crud_device
from app.schemas.attendance import AttendanceCreate, Attendance
from app.schemas.device_command import DeviceCommandCode, DeviceCommandType, COMMAND_TYPE_TO_CODE
from app.schemas.device import DeviceHeartbeatUpdate
from app.db.session import SessionLocal
from app.websocket.connection_manager import manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_greeting() -> str:
    """Return appropriate greeting based on current time."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Bonjour"
    elif 12 <= hour < 18:
        return "Bon après-midi"
    else:
        return "Bonsoir"


# Récupérer la boucle d'événements asyncio principale
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)


class MQTTClient:
    """
    Client MQTT pour la gestion des appareils IoT.

    Topics MQTT:
    - kuilinga/devices/{serial}/attendance : Réception des pointages (badge_id)
    - kuilinga/devices/{serial}/response : Envoi des réponses de validation
    - kuilinga/devices/{serial}/command : Envoi des commandes administratives
    - kuilinga/devices/{serial}/status : Réception du statut des appareils
    """

    # Topics MQTT
    TOPIC_ATTENDANCE = "kuilinga/devices/{serial}/attendance"
    TOPIC_RESPONSE = "kuilinga/devices/{serial}/response"
    TOPIC_COMMAND = "kuilinga/devices/{serial}/command"
    TOPIC_STATUS = "kuilinga/devices/{serial}/status"

    def __init__(self):
        # Utiliser la version callback_api_version pour éviter les warnings
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
            client_id=f"kuilinga-backend-{datetime.now().timestamp()}"
        )
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.connected = False

        # Configuration authentification
        if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

        # Configuration SSL/TLS
        self._configure_tls()

    def _configure_tls(self):
        """Configure SSL/TLS pour la connexion MQTT sécurisée."""
        if not settings.MQTT_TLS_ENABLED:
            logger.info("MQTT TLS désactivé")
            return

        logger.info("Configuration SSL/TLS pour MQTT...")

        # Chemins des certificats (configurables via settings)
        ca_cert = getattr(settings, 'MQTT_CA_CERT', None)
        client_cert = getattr(settings, 'MQTT_CLIENT_CERT', None)
        client_key = getattr(settings, 'MQTT_CLIENT_KEY', None)

        try:
            if ca_cert and Path(ca_cert).exists():
                # Configuration complète avec certificats personnalisés
                self.client.tls_set(
                    ca_certs=ca_cert,
                    certfile=client_cert if client_cert and Path(client_cert).exists() else None,
                    keyfile=client_key if client_key and Path(client_key).exists() else None,
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLS,
                )
                logger.info(f"TLS configuré avec certificat CA: {ca_cert}")

                if client_cert:
                    logger.info(f"Certificat client configuré: {client_cert}")
            else:
                # Configuration TLS basique (utilise les CA du système)
                self.client.tls_set(
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLS,
                )
                logger.info("TLS configuré avec les certificats système")

            # Option pour ignorer la vérification du hostname (dev uniquement)
            if getattr(settings, 'MQTT_TLS_INSECURE', False):
                self.client.tls_insecure_set(True)
                logger.warning("ATTENTION: Vérification TLS du hostname désactivée (mode développement)")

        except Exception as e:
            logger.error(f"Erreur configuration TLS: {e}")
            raise

    def connect(self):
        """Établit la connexion au broker MQTT."""
        logger.info(f"Connexion au broker MQTT: {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
        try:
            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
        except Exception as e:
            logger.error(f"Échec de connexion MQTT: {e}")
            raise

    def start(self):
        """Démarre le client MQTT en mode non-bloquant."""
        self.connect()
        self.client.loop_start()

    def stop(self):
        """Arrête le client MQTT proprement."""
        logger.info("Arrêt du client MQTT...")
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False

    def on_connect(self, client, userdata, flags, rc):
        """Callback appelé lors de la connexion au broker."""
        if rc == 0:
            logger.info("Connecté au broker MQTT avec succès")
            self.connected = True

            # S'abonner aux topics de pointage et de statut
            attendance_topic = "kuilinga/devices/+/attendance"
            status_topic = "kuilinga/devices/+/status"

            client.subscribe(attendance_topic)
            client.subscribe(status_topic)

            logger.info(f"Abonné aux topics: {attendance_topic}, {status_topic}")
        else:
            error_messages = {
                1: "Version de protocole incorrecte",
                2: "Identifiant client invalide",
                3: "Serveur indisponible",
                4: "Mauvais nom d'utilisateur ou mot de passe",
                5: "Non autorisé",
            }
            error_msg = error_messages.get(rc, f"Code d'erreur inconnu: {rc}")
            logger.error(f"Échec de connexion MQTT: {error_msg}")
            self.connected = False

    def on_disconnect(self, client, userdata, rc):
        """Callback appelé lors de la déconnexion."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Déconnexion inattendue du broker MQTT (code: {rc})")
        else:
            logger.info("Déconnecté du broker MQTT")

    def on_message(self, client, userdata, msg):
        """Callback appelé à la réception d'un message MQTT."""
        logger.info(f"Message reçu sur {msg.topic}: {msg.payload.decode()}")

        try:
            topic_parts = msg.topic.split('/')
            if len(topic_parts) < 4:
                logger.error(f"Format de topic invalide: {msg.topic}")
                return

            device_serial = topic_parts[2]
            message_type = topic_parts[3]

            if message_type == "attendance":
                self._handle_attendance_message(client, device_serial, msg.payload)
            elif message_type == "status":
                self._handle_status_message(device_serial, msg.payload)
            else:
                logger.warning(f"Type de message non géré: {message_type}")

        except Exception as e:
            logger.error(f"Erreur traitement message MQTT: {e}", exc_info=True)

    def _handle_attendance_message(self, client, device_serial: str, payload: bytes):
        """
        Traite un message de pointage depuis un appareil IoT.

        Logique de validation:
        1. Vérifie si l'appareil existe → sinon ignore
        2. Vérifie si le badge existe → REJECTED (0x108080)
        3. Vérifie si l'employé/badge est actif → REFUSED (0x003020)
        4. Enregistre le pointage → ACCEPTED (0x001020)
        """
        try:
            data = json.loads(payload.decode())
            badge_id = data.get("badge_id")

            if not badge_id:
                logger.error("Message de pointage sans badge_id")
                return

            with SessionLocal() as db:
                # 1. Vérifier l'appareil
                device = crud_device.get_by_serial(db, serial_number=device_serial)
                if not device:
                    logger.error(f"Appareil inconnu: {device_serial}")
                    return

                # Mettre à jour last_seen_at car le device communique
                crud_device.update_last_seen(db, device=device)

                # 2. Vérifier le badge/employé
                employee = crud_employee.get_by_badge(db, badge_id=badge_id)

                if not employee:
                    # Badge non trouvé en base → REJECTED
                    logger.warning(f"Badge inconnu: {badge_id}")
                    self._send_validation_response(
                        client, device_serial,
                        DeviceCommandCode.REJECTED,
                        "Badge non reconnu"
                    )
                    return

                # 3. Vérifier si l'employé est actif (si le champ existe)
                is_active = getattr(employee, 'is_active', True)
                badge_active = getattr(employee, 'badge_active', True)

                if not is_active or not badge_active:
                    # Badge désactivé par l'admin → REFUSED
                    logger.warning(f"Badge désactivé: {badge_id} (employé: {employee.id})")
                    self._send_validation_response(
                        client, device_serial,
                        DeviceCommandCode.REFUSED,
                        "Badge désactivé",
                        employee_name=f"{employee.first_name} {employee.last_name}"
                    )
                    return

                # 4. Enregistrer le pointage → ACCEPTED
                attendance_in = AttendanceCreate(
                    timestamp=data.get("timestamp", datetime.now().isoformat()),
                    type=data.get("type", "in"),
                    employee_id=employee.id,
                    device_id=device.id,
                )

                new_attendance = crud_attendance.create(db, obj_in=attendance_in)
                logger.info(f"Pointage enregistré pour {employee.first_name} {employee.last_name}")

                # Envoyer la réponse ACCEPTED avec salutation
                greeting = get_greeting()
                employee_name = f"{employee.first_name} {employee.last_name}"

                self._send_validation_response(
                    client, device_serial,
                    DeviceCommandCode.ACCEPTED,
                    f"{greeting} {employee_name}",
                    employee_name=employee_name,
                    attendance_type=data.get("type", "in")
                )

                # Diffuser via WebSocket
                self._broadcast_attendance(db, new_attendance)

        except json.JSONDecodeError as e:
            logger.error(f"JSON invalide dans le message de pointage: {e}")
        except Exception as e:
            logger.error(f"Erreur traitement pointage: {e}", exc_info=True)

    def _send_validation_response(
        self,
        client,
        device_serial: str,
        code: DeviceCommandCode,
        message: str,
        employee_name: Optional[str] = None,
        attendance_type: Optional[str] = None
    ):
        """
        Envoie une réponse de validation à l'appareil.

        Le code hexadécimal est envoyé dans le champ 'code'.
        """
        response_topic = self.TOPIC_RESPONSE.format(serial=device_serial)

        response_payload = {
            "code": code.value,  # Code hexadécimal (ex: "0x001020")
            "status": code.name,  # Nom du statut (ex: "ACCEPTED")
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

        if employee_name:
            response_payload["employee_name"] = employee_name
        if attendance_type:
            response_payload["attendance_type"] = attendance_type

        client.publish(response_topic, json.dumps(response_payload), retain=False)
        logger.info(f"Réponse envoyée à {response_topic}: {code.name} ({code.value})")

    def _handle_status_message(self, device_serial: str, payload: bytes):
        """
        Traite un message de statut/heartbeat reçu d'un appareil IoT.

        Format attendu du payload:
        {
            "status": "online",
            "firmware_version": "2.1.0",
            "battery_level": 85,
            "wifi_rssi": -45,
            "timestamp": "2024-01-15T10:05:00Z"
        }
        """
        try:
            data = json.loads(payload.decode())
            logger.info(f"Heartbeat reçu de {device_serial}: {data}")

            with SessionLocal() as db:
                device = crud_device.get_by_serial(db, serial_number=device_serial)
                if not device:
                    logger.warning(f"Heartbeat ignoré - appareil inconnu: {device_serial}")
                    return

                # Construire l'objet de mise à jour du heartbeat
                heartbeat_data = DeviceHeartbeatUpdate(
                    last_seen_at=datetime.now(),
                    firmware_version=data.get("firmware_version"),
                    battery_level=data.get("battery_level"),
                    wifi_rssi=data.get("wifi_rssi")
                )

                # Mettre à jour le device en base
                crud_device.update_heartbeat(
                    db,
                    device=device,
                    heartbeat_data=heartbeat_data
                )

                logger.info(
                    f"Appareil {device_serial} mis à jour: ONLINE, "
                    f"firmware={heartbeat_data.firmware_version}, "
                    f"battery={heartbeat_data.battery_level}%, "
                    f"rssi={heartbeat_data.wifi_rssi}dBm"
                )

        except json.JSONDecodeError as e:
            logger.error(f"JSON invalide dans le heartbeat de {device_serial}: {e}")
        except Exception as e:
            logger.error(f"Erreur traitement heartbeat: {e}", exc_info=True)

    def _broadcast_attendance(self, db: Session, attendance):
        """Diffuse un nouveau pointage via WebSocket."""
        try:
            db.refresh(attendance)
            enriched = crud_attendance.get(db, id=attendance.id)

            if enriched:
                attendance_schema = Attendance.from_orm(enriched)
                message = {
                    "type": "new_attendance",
                    "payload": attendance_schema.dict()
                }

                future = asyncio.run_coroutine_threadsafe(
                    manager.broadcast(json.dumps(message, default=str)),
                    loop
                )
                future.result()

        except Exception as e:
            logger.error(f"Erreur broadcast WebSocket: {e}")

    def send_command(self, device_serial: str, command: DeviceCommandType) -> bool:
        """
        Envoie une commande administrative à un appareil.

        Args:
            device_serial: Numéro de série de l'appareil
            command: Type de commande (RESET, REBOOT, SLEEP, STATUS)

        Returns:
            True si la commande a été envoyée, False sinon
        """
        if not self.connected:
            logger.error("Client MQTT non connecté")
            return False

        command_code = COMMAND_TYPE_TO_CODE.get(command)
        if not command_code:
            logger.error(f"Commande inconnue: {command}")
            return False

        topic = self.TOPIC_COMMAND.format(serial=device_serial)

        payload = {
            "code": command_code.value,  # Code hexadécimal
            "command": command.value,     # Nom de la commande
            "timestamp": datetime.now().isoformat()
        }

        try:
            result = self.client.publish(topic, json.dumps(payload), qos=1)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Commande {command.value} ({command_code.value}) envoyée à {device_serial}")
                return True
            else:
                logger.error(f"Échec envoi commande: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"Erreur envoi commande: {e}")
            return False

    def send_command_by_code(self, device_serial: str, code: str) -> bool:
        """
        Envoie un code hexadécimal brut à un appareil.

        Args:
            device_serial: Numéro de série de l'appareil
            code: Code hexadécimal (ex: "0x108090")

        Returns:
            True si la commande a été envoyée, False sinon
        """
        if not self.connected:
            logger.error("Client MQTT non connecté")
            return False

        topic = self.TOPIC_COMMAND.format(serial=device_serial)

        payload = {
            "code": code,
            "timestamp": datetime.now().isoformat()
        }

        try:
            result = self.client.publish(topic, json.dumps(payload), qos=1)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"Erreur envoi code: {e}")
            return False

    def is_connected(self) -> bool:
        """Vérifie si le client est connecté au broker."""
        return self.connected


# Instance globale du client MQTT
mqtt_client = MQTTClient()
