"""
Schémas pour les commandes IoT envoyées aux appareils via MQTT.

Les codes hexadécimaux correspondent aux commandes définies côté firmware:
- ACCEPTED (0x001020): Badge reconnu et autorisé
- REFUSED (0x003020): Badge désactivé par l'admin
- REJECTED (0x108080): Badge inconnu (non trouvé en base)
- RESET (0x108070): Réinitialiser l'appareil
- REBOOT (0x108090): Redémarrer l'appareil
- SLEEP (0x1080B0): Mettre l'appareil en veille
- STATUS (0x100010): Demander le statut de l'appareil
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class DeviceCommandCode(str, Enum):
    """Codes hexadécimaux des commandes pour les appareils IoT."""
    ACCEPTED = "0x001020"
    REFUSED = "0x003020"
    RESET = "0x108070"
    REJECTED = "0x108080"
    REBOOT = "0x108090"
    SLEEP = "0x1080B0"
    STATUS = "0x100010"


class DeviceCommandType(str, Enum):
    """Types de commandes administratives (noms lisibles)."""
    RESET = "reset"
    REBOOT = "reboot"
    SLEEP = "sleep"
    STATUS = "status"


# Mapping des types de commande vers les codes hexadécimaux
COMMAND_TYPE_TO_CODE = {
    DeviceCommandType.RESET: DeviceCommandCode.RESET,
    DeviceCommandType.REBOOT: DeviceCommandCode.REBOOT,
    DeviceCommandType.SLEEP: DeviceCommandCode.SLEEP,
    DeviceCommandType.STATUS: DeviceCommandCode.STATUS,
}


class DeviceCommandRequest(BaseModel):
    """Requête pour envoyer une commande à un appareil."""
    command: DeviceCommandType = Field(
        ...,
        description="Type de commande à envoyer (reset, reboot, sleep, status)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "command": "reboot"
            }
        }


class DeviceCommandResponse(BaseModel):
    """Réponse après envoi d'une commande à un appareil."""
    success: bool = Field(..., description="Indique si la commande a été envoyée")
    device_id: str = Field(..., description="ID du terminal")
    device_serial: str = Field(..., description="Numéro de série du terminal")
    command: str = Field(..., description="Type de commande envoyée")
    command_code: str = Field(..., description="Code hexadécimal envoyé")
    message: str = Field(..., description="Message de confirmation")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "device_id": "uuid-device-123",
                "device_serial": "SN-DEVICE-001",
                "command": "reboot",
                "command_code": "0x108090",
                "message": "Commande REBOOT envoyée au terminal SN-DEVICE-001"
            }
        }


class BadgeValidationResponse(BaseModel):
    """Réponse de validation d'un badge envoyée à l'appareil."""
    code: str = Field(..., description="Code hexadécimal de la réponse")
    status: str = Field(..., description="Statut lisible (ACCEPTED, REFUSED, REJECTED)")
    message: str = Field(..., description="Message pour l'appareil")
    employee_name: Optional[str] = Field(None, description="Nom de l'employé si trouvé")
    timestamp: str = Field(..., description="Horodatage de la réponse")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "0x001020",
                "status": "ACCEPTED",
                "message": "Bonjour Jean Dupont",
                "employee_name": "Jean Dupont",
                "timestamp": "2024-01-15T08:30:00Z"
            }
        }


class DeviceBulkCommandRequest(BaseModel):
    """Requête pour envoyer une commande à plusieurs appareils."""
    device_ids: list[str] = Field(
        ...,
        description="Liste des IDs des terminaux",
        min_length=1
    )
    command: DeviceCommandType = Field(
        ...,
        description="Type de commande à envoyer"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "device_ids": ["uuid-device-1", "uuid-device-2"],
                "command": "status"
            }
        }


class DeviceBulkCommandResponse(BaseModel):
    """Réponse après envoi d'une commande à plusieurs appareils."""
    success: bool = Field(..., description="Indique si toutes les commandes ont été envoyées")
    total_devices: int = Field(..., description="Nombre total d'appareils ciblés")
    successful: int = Field(..., description="Nombre de commandes envoyées avec succès")
    failed: int = Field(..., description="Nombre d'échecs")
    results: list[DeviceCommandResponse] = Field(..., description="Détails par appareil")
