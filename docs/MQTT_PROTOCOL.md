# Protocole MQTT - Communication avec les Terminaux IoT

Ce document décrit le protocole de communication MQTT entre le backend Kuilinga et les terminaux IoT de pointage.

## Table des matières

1. [Configuration](#configuration)
2. [Topics MQTT](#topics-mqtt)
3. [Codes hexadécimaux](#codes-hexadécimaux)
4. [Flux de communication](#flux-de-communication)
5. [Format des messages](#format-des-messages)
6. [Sécurité SSL/TLS](#sécurité-ssltls)

---

## Configuration

### Variables d'environnement

```env
# Connexion au broker
MQTT_BROKER_HOST=mqtt.example.com
MQTT_BROKER_PORT=8883
MQTT_USERNAME=kuilinga_backend
MQTT_PASSWORD=secret_password
MQTT_TLS_ENABLED=True

# Certificats SSL (optionnel)
MQTT_CA_CERT=certs/ca.crt
MQTT_CLIENT_CERT=certs/client.crt
MQTT_CLIENT_KEY=certs/client.key
MQTT_TLS_INSECURE=False
```

### Ports standards

| Port | Usage |
|------|-------|
| 1883 | MQTT non chiffré (développement uniquement) |
| 8883 | MQTT over TLS (production) |

---

## Topics MQTT

### Structure des topics

```
kuilinga/devices/{serial_number}/{message_type}
```

| Topic | Direction | Description |
|-------|-----------|-------------|
| `kuilinga/devices/{serial}/attendance` | Terminal → Backend | Réception des pointages |
| `kuilinga/devices/{serial}/response` | Backend → Terminal | Réponses de validation |
| `kuilinga/devices/{serial}/command` | Backend → Terminal | Commandes administratives |
| `kuilinga/devices/{serial}/status` | Terminal → Backend | Statut de l'appareil |

### Wildcards utilisés

Le backend s'abonne aux topics suivants au démarrage :
- `kuilinga/devices/+/attendance` - Tous les pointages
- `kuilinga/devices/+/status` - Tous les statuts

---

## Codes hexadécimaux

### Réponses de validation de badge

Ces codes sont envoyés au terminal après la lecture d'un badge.

| Code | Nom | Description | Condition |
|------|-----|-------------|-----------|
| `0x001020` | ACCEPTED | Badge autorisé | Badge trouvé, employé actif |
| `0x003020` | REFUSED | Badge désactivé | Badge trouvé mais désactivé par l'admin |
| `0x108080` | REJECTED | Badge inconnu | Badge non trouvé en base de données |

### Commandes administratives

Ces codes sont envoyés depuis le frontend via l'API REST.

| Code | Nom | Description | Action sur le terminal |
|------|-----|-------------|------------------------|
| `0x108070` | RESET | Réinitialiser | Remet les paramètres par défaut |
| `0x108090` | REBOOT | Redémarrer | Redémarre le terminal |
| `0x1080B0` | SLEEP | Mise en veille | Passe en mode basse consommation |
| `0x100010` | STATUS | Demande statut | Le terminal envoie ses infos |

---

## Flux de communication

### 1. Pointage d'un badge (flux normal)

```
┌──────────┐                    ┌──────────┐                    ┌──────────┐
│ Terminal │                    │ Backend  │                    │ Frontend │
└────┬─────┘                    └────┬─────┘                    └────┬─────┘
     │                               │                               │
     │ 1. Badge scanné               │                               │
     │ ─────────────────────────────>│                               │
     │ Topic: .../attendance         │                               │
     │ {badge_id, type, timestamp}   │                               │
     │                               │                               │
     │                               │ 2. Vérification en BDD        │
     │                               │ ───────────────────────>      │
     │                               │                               │
     │                               │ 3. Enregistrement pointage    │
     │                               │ <───────────────────────      │
     │                               │                               │
     │ 4. Réponse ACCEPTED           │                               │
     │ <─────────────────────────────│                               │
     │ Topic: .../response           │                               │
     │ {code: "0x001020", message}   │                               │
     │                               │                               │
     │                               │ 5. WebSocket broadcast        │
     │                               │ ─────────────────────────────>│
     │                               │ {type: "new_attendance"}      │
     │                               │                               │
```

### 2. Badge inconnu (REJECTED)

```
┌──────────┐                    ┌──────────┐
│ Terminal │                    │ Backend  │
└────┬─────┘                    └────┬─────┘
     │                               │
     │ Badge scanné                  │
     │ ─────────────────────────────>│
     │ {badge_id: "UNKNOWN-123"}     │
     │                               │
     │                               │ Badge non trouvé en BDD
     │                               │
     │ Réponse REJECTED              │
     │ <─────────────────────────────│
     │ {code: "0x108080",            │
     │  status: "REJECTED",          │
     │  message: "Badge non reconnu"}│
     │                               │
```

### 3. Badge désactivé (REFUSED)

```
┌──────────┐                    ┌──────────┐
│ Terminal │                    │ Backend  │
└────┬─────┘                    └────┬─────┘
     │                               │
     │ Badge scanné                  │
     │ ─────────────────────────────>│
     │ {badge_id: "EMP-456"}         │
     │                               │
     │                               │ Badge trouvé mais is_active=False
     │                               │
     │ Réponse REFUSED               │
     │ <─────────────────────────────│
     │ {code: "0x003020",            │
     │  status: "REFUSED",           │
     │  message: "Badge désactivé",  │
     │  employee_name: "Jean Dupont"}│
     │                               │
```

### 4. Envoi d'une commande administrative

```
┌──────────┐                    ┌──────────┐                    ┌──────────┐
│ Frontend │                    │ Backend  │                    │ Terminal │
└────┬─────┘                    └────┬─────┘                    └────┬─────┘
     │                               │                               │
     │ POST /devices/{id}/reboot     │                               │
     │ ─────────────────────────────>│                               │
     │                               │                               │
     │                               │ Publish commande MQTT         │
     │                               │ ─────────────────────────────>│
     │                               │ Topic: .../command            │
     │                               │ {code: "0x108090"}            │
     │                               │                               │
     │ Réponse HTTP 200              │                               │
     │ <─────────────────────────────│                               │
     │ {success: true,               │                               │
     │  command_code: "0x108090"}    │                               │
     │                               │                               │
     │                               │         Terminal redémarre    │
     │                               │                               │
     │                               │ Status après reboot           │
     │                               │ <─────────────────────────────│
     │                               │ Topic: .../status             │
     │                               │ {status: "online", ...}       │
     │                               │                               │
```

---

## Format des messages

### Message de pointage (Terminal → Backend)

**Topic:** `kuilinga/devices/{serial}/attendance`

```json
{
  "badge_id": "EMP-BADGE-123",
  "type": "in",
  "timestamp": "2024-01-15T08:30:00Z"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `badge_id` | string | Identifiant du badge (lu par le terminal) |
| `type` | string | Type de pointage : `"in"` (entrée) ou `"out"` (sortie) |
| `timestamp` | string | Horodatage ISO 8601 (optionnel, sinon horodatage serveur) |

### Réponse de validation (Backend → Terminal)

**Topic:** `kuilinga/devices/{serial}/response`

```json
{
  "code": "0x001020",
  "status": "ACCEPTED",
  "message": "Bonjour Jean Dupont",
  "employee_name": "Jean Dupont",
  "attendance_type": "in",
  "timestamp": "2024-01-15T08:30:01Z"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `code` | string | Code hexadécimal de la réponse |
| `status` | string | Nom du statut (ACCEPTED, REFUSED, REJECTED) |
| `message` | string | Message à afficher sur le terminal |
| `employee_name` | string | Nom de l'employé (si trouvé) |
| `attendance_type` | string | Type de pointage enregistré |
| `timestamp` | string | Horodatage de la réponse |

### Commande administrative (Backend → Terminal)

**Topic:** `kuilinga/devices/{serial}/command`

```json
{
  "code": "0x108090",
  "command": "reboot",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `code` | string | Code hexadécimal de la commande |
| `command` | string | Nom de la commande (optionnel) |
| `timestamp` | string | Horodatage de la commande |

### Message de statut (Terminal → Backend)

**Topic:** `kuilinga/devices/{serial}/status`

```json
{
  "status": "online",
  "firmware_version": "2.1.0",
  "battery_level": 85,
  "last_sync": "2024-01-15T08:00:00Z",
  "wifi_rssi": -45,
  "timestamp": "2024-01-15T10:05:00Z"
}
```

*Note: Le format exact dépend du firmware du terminal.*

---

## Sécurité SSL/TLS

### Configuration avec certificats

Pour une connexion sécurisée, configurez les certificats dans `.env` :

```env
MQTT_TLS_ENABLED=True
MQTT_CA_CERT=certs/ca.crt
MQTT_CLIENT_CERT=certs/client.crt
MQTT_CLIENT_KEY=certs/client.key
```

### Structure des fichiers de certificats

```
kuilinga-backend/
├── certs/
│   ├── ca.crt           # Certificat de l'autorité de certification
│   ├── client.crt       # Certificat client (authentification mutuelle)
│   └── client.key       # Clé privée du certificat client
```

### Obtention des certificats

Les certificats doivent être fournis par :
1. Le fournisseur des terminaux IoT
2. Ou générés par votre infrastructure PKI

### Vérification TLS

En production, toujours garder `MQTT_TLS_INSECURE=False` pour vérifier :
- La validité du certificat du broker
- La correspondance du hostname

---

## QoS (Quality of Service)

| Message | QoS | Raison |
|---------|-----|--------|
| Pointages | 1 | Garantir la livraison au moins une fois |
| Réponses | 0 | Pas critique si perdu (terminal peut réessayer) |
| Commandes | 1 | Garantir la livraison de la commande |
| Statuts | 0 | Informationnel, peut être perdu |

---

## Gestion des erreurs

### Terminal inconnu

Si un message arrive d'un terminal non enregistré :
- Le backend log l'erreur
- Aucune réponse n'est envoyée
- Le message est ignoré

### Broker déconnecté

- Le backend tente une reconnexion automatique
- Les endpoints API retournent une erreur 503
- L'indicateur MQTT dans le frontend passe au rouge

### Timeout de commande

Les commandes n'ont pas de confirmation directe. Pour vérifier l'exécution :
1. Envoyer une commande STATUS après quelques secondes
2. Écouter les messages de statut du terminal

---

## Test avec mosquitto

### Simuler un pointage

```bash
mosquitto_pub -h localhost -p 1883 \
  -t "kuilinga/devices/SN-TEST-001/attendance" \
  -m '{"badge_id": "EMP-123", "type": "in"}'
```

### Écouter les réponses

```bash
mosquitto_sub -h localhost -p 1883 \
  -t "kuilinga/devices/SN-TEST-001/response" -v
```

### Écouter les commandes

```bash
mosquitto_sub -h localhost -p 1883 \
  -t "kuilinga/devices/SN-TEST-001/command" -v
```

### Simuler un statut de terminal

```bash
mosquitto_pub -h localhost -p 1883 \
  -t "kuilinga/devices/SN-TEST-001/status" \
  -m '{"status": "online", "firmware": "2.0"}'
```
