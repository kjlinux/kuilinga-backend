# Intégration des Appareils IoT

Ce document décrit comment les appareils IoT peuvent envoyer des données de pointage au système KUILINGA, soit via des requêtes HTTP, soit via le protocole MQTT.

## Scénarios d'Intégration

Les appareils IoT, tels que les lecteurs de badges, les pointeuses biométriques ou d'autres capteurs, doivent être enregistrés dans le système avant de pouvoir soumettre des données. Chaque appareil se voit attribuer un numéro de série unique lors de son enregistrement. De même, chaque employé doit être enregistré avec un identifiant de badge unique.

La transmission des données de pointage peut se faire de deux manières :

1.  **HTTP/HTTPS** : L'appareil envoie une requête POST à un point de terminaison (endpoint) spécifique de l'API. Cette méthode est simple et bien adaptée aux appareils disposant d'une connectivité Internet stable.
2.  **MQTT** : L'appareil publie un message sur un sujet (topic) MQTT spécifique. Cette méthode est recommandée pour les environnements où la connectivité réseau est instable ou pour la communication en temps réel à faible latence.

## Authentification

L'authentification et l'identification des appareils sont gérées différemment selon le protocole utilisé :

- **Pour HTTP**, la sécurité est assurée par un **jeton d'accès (API Key ou JWT)** qui doit être inclus dans l'en-tête de chaque requête. De plus, l'API est protégée par des permissions granulaires (par exemple, `attendance:create`).
- **Pour MQTT**, l'identification de l'appareil est basée sur le **numéro de série** inclus dans le sujet MQTT (`kuilinga/devices/{device_serial}/attendance`). La sécurité du broker (authentification et chiffrement TLS) est configurée au niveau de l'infrastructure.

Ci-dessous, les détails techniques pour chaque méthode.

## Méthode 1 : Intégration via HTTP/HTTPS

Cette méthode consiste à envoyer les données de pointage via une requête HTTP POST à l'API du système.

### Point de terminaison (Endpoint)

- **URL** : `/api/v1/attendances/`
- **Méthode** : `POST`

### En-têtes (Headers)

Chaque requête doit inclure les en-têtes suivants pour l'authentification et la spécification du contenu :

- `Content-Type`: `application/json`
- `Authorization`: `Bearer <VOTRE_JETON_JWT>`

Le jeton JWT doit être obtenu par un utilisateur ou un service disposant de la permission `attendance:create`.

### Corps de la Requête (Payload)

Le corps de la requête doit être un objet JSON contenant les informations du pointage. Voici la structure détaillée :

```json
{
  "timestamp": "2023-10-27T10:00:00Z",
  "type": "in",
  "employee_id": "c7a7c5e2-4f9a-4a8e-b1e3-8e6d2b5c8a1d",
  "device_id": "f2b8c2a8-6e3a-4e2b-8b1e-9e7d3c6a4b1f"
}
```

### Description des Champs

| Champ         | Type   | Obligatoire | Description                                                                |
| ------------- | ------ | ----------- | -------------------------------------------------------------------------- |
| `timestamp`   | string | Oui         | La date et l'heure du pointage au format ISO 8601 (UTC).                   |
| `type`        | string | Oui         | Le type de pointage. Doit être soit `"in"` (entrée) soit `"out"` (sortie). |
| `employee_id` | string | Oui         | L'identifiant unique (UUID) de l'employé associé au badge scanné.          |
| `device_id`   | string | Oui         | L'identifiant unique (UUID) de l'appareil qui a enregistré le pointage.    |

### Exemple de Commande `curl`

Voici un exemple de requête utilisant `curl` pour envoyer un pointage :

```bash
curl -X POST "http://votre-domaine.com/api/v1/attendances/" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer <VOTRE_JETON_JWT>" \
-d '{
  "timestamp": "2023-10-27T10:00:00Z",
  "type": "in",
  "employee_id": "c7a7c5e2-4f9a-4a8e-b1e3-8e6d2b5c8a1d",
  "device_id": "f2b8c2a8-6e3a-4e2b-8b1e-9e7d3c6a4b1f"
}'
```

### Réponse de l'API

- **En cas de succès (Code `201 Created`)** : L'API retourne l'objet du pointage nouvellement créé, incluant les détails de l'employé, du site, etc.
- **En cas d'erreur (Codes `4xx`)** : L'API retourne un message d'erreur détaillé, par exemple si l'employé ou l'appareil n'est pas trouvé, ou si les données sont invalides.

## Méthode 2 : Intégration via MQTT

Le protocole MQTT est idéal pour les communications en temps réel et les environnements à faible bande passante.

### Paramètres du Broker MQTT

- **Hôte** : `mqtt.votre-domaine.com` (à remplacer par l'adresse du broker HiveMQ)
- **Port** : `1883` (port standard non chiffré) ou `8883` (pour une connexion TLS)
- **Authentification** : Nom d'utilisateur et mot de passe (Ils seront configurés sur le broker)
- **TLS** : Recommandé pour la production

### Sujet (Topic) MQTT

Les appareils doivent publier les messages de pointage sur un sujet dynamique qui inclut leur propre numéro de série.

- **Structure du sujet** : `kuilinga/devices/{device_serial}/attendance`

Où `{device_serial}` doit être remplacé par le numéro de série unique de l'appareil IoT. Par exemple, pour un appareil avec le numéro de série `DEV-00123`, le sujet sera :

`kuilinga/devices/DEV-00123/attendance`

### Format du Message (Payload)

Le message publié doit être un objet JSON contenant les informations du pointage. Contrairement à l'API HTTP, le message MQTT utilise l'identifiant du badge de l'employé (`badge_id`) au lieu de son UUID. Le système se charge de faire la correspondance.

```json
{
  "timestamp": "2023-10-27T10:01:00Z",
  "type": "in",
  "badge_id": "EMP-BADGE-456"
}
```

### Description des Champs

| Champ       | Type   | Obligatoire | Description                                              |
| ----------- | ------ | ----------- | -------------------------------------------------------- |
| `timestamp` | string | Oui         | La date et l'heure du pointage au format ISO 8601 (UTC). |
| `type`      | string | Oui         | Le type de pointage : `"in"` ou `"out"`.                 |
| `badge_id`  | string | Oui         | L'identifiant unique du badge présenté par l'employé.    |

### Logique de Traitement

1.  L'appareil publie le message JSON sur le sujet MQTT approprié.
2.  Le backend de KUILINGA, abonné à `kuilinga/devices/+/attendance`, reçoit le message.
3.  Le système extrait le `{device_serial}` du sujet pour identifier l'appareil.
4.  Il recherche l'employé correspondant au `badge_id` fourni dans le message.
5.  Il enregistre le pointage dans la base de données.
6.  Enfin, il diffuse l'événement de nouveau pointage à tous les clients connectés via WebSocket pour une mise à jour en temps réel des interfaces.

Cette approche permet une communication asynchrone et découplée, ce qui la rend robuste face aux interruptions de réseau.
