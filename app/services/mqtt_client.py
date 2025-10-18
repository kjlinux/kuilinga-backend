import json
import logging
import asyncio
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from app.config import settings
from app.crud import attendance as crud_attendance
from app.crud import employee as crud_employee
from app.crud import device as crud_device
from app.schemas.attendance import AttendanceCreate, Attendance
from app.db.session import SessionLocal
from app.websocket.connection_manager import manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Récupérer la boucle d'événements asyncio principale
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)


class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
        if settings.MQTT_TLS_ENABLED:
            self.client.tls_set()

    def connect(self):
        logger.info(f"Connecting to MQTT Broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
        self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)

    def start(self):
        self.connect()
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Successfully connected to MQTT Broker.")
            topic = "kuilinga/devices/+/attendance"
            client.subscribe(topic)
            logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect, return code {rc}\n")

    def on_message(self, client, userdata, msg):
        logger.info(f"Received message on topic {msg.topic}: {msg.payload.decode()}")
        try:
            device_serial = msg.topic.split('/')[2]
            payload = json.loads(msg.payload.decode())

            with SessionLocal() as db:
                device = crud_device.get_by_serial(db, serial_number=device_serial)
                if not device:
                    logger.error(f"Device with serial '{device_serial}' not found.")
                    return

                employee = crud_employee.get_by_badge(db, badge_id=payload.get("badge_id"))
                if not employee:
                    logger.error(f"Employee with badge_id '{payload.get('badge_id')}' not found.")
                    return

                attendance_in = AttendanceCreate(
                    timestamp=payload.get("timestamp"),
                    type=payload.get("type", "in"),
                    employee_id=employee.id,
                    device_id=device.id,
                )

                new_attendance = crud_attendance.create(db, obj_in=attendance_in)
                logger.info(f"Recorded attendance for employee {employee.id}")

                # Re-fetch with relationships for the broadcast
                db.refresh(new_attendance)
                enriched_attendance = crud.attendance.get(db, id=new_attendance.id)

                # Diffuser le nouveau pointage via WebSocket
                if enriched_attendance:
                    attendance_schema = Attendance.from_orm(enriched_attendance)
            message = {
                "type": "new_attendance",
                "payload": attendance_schema.dict()
            }

            # Appeler la coroutine broadcast de manière thread-safe
            future = asyncio.run_coroutine_threadsafe(manager.broadcast(json.dumps(message, default=str)), loop)
            future.result() # Attendre que la coroutine se termine si nécessaire

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")


mqtt_client = MQTTClient()
