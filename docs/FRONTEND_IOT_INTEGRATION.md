# Guide d'Intégration Frontend - Gestion des Terminaux IoT

Ce document décrit comment implémenter les fonctionnalités de gestion des terminaux IoT dans le frontend Kuilinga.

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Codes de commande IoT](#codes-de-commande-iot)
3. [Endpoints API disponibles](#endpoints-api-disponibles)
4. [Statut des terminaux (Heartbeat)](#statut-des-terminaux-heartbeat)
5. [Implémentation Frontend](#implémentation-frontend)
6. [Gestion des WebSockets](#gestion-des-websockets)
7. [Configuration SSL/TLS](#configuration-ssltls)
8. [Exemples de code](#exemples-de-code)

---

## Vue d'ensemble

Le système permet de :
- **Envoyer des commandes** aux terminaux IoT (redémarrage, réinitialisation, mise en veille, statut)
- **Recevoir les réponses** de validation des badges en temps réel
- **Monitorer** l'état de connexion des terminaux

### Architecture de communication

```
┌─────────────┐     HTTP/REST      ┌──────────────┐      MQTT       ┌─────────────┐
│   Frontend  │ ◄──────────────► │   Backend    │ ◄──────────────► │  Terminal   │
│   (React)   │                   │   (FastAPI)  │                  │    IoT      │
└─────────────┘                   └──────────────┘                  └─────────────┘
       ▲                                 │
       │         WebSocket               │
       └─────────────────────────────────┘
              (notifications temps réel)
```

---

## Codes de commande IoT

Les terminaux IoT utilisent des **codes hexadécimaux** pour les commandes et réponses :

### Réponses de validation de badge

| Code | Nom | Description | Quand c'est envoyé |
|------|-----|-------------|-------------------|
| `0x001020` | ACCEPTED | Badge reconnu et autorisé | Badge valide, employé actif |
| `0x003020` | REFUSED | Badge désactivé par l'admin | Badge trouvé mais employé/badge désactivé |
| `0x108080` | REJECTED | Badge inconnu | Badge non trouvé en base de données |

### Commandes administratives

| Code | Nom | Description | Action |
|------|-----|-------------|--------|
| `0x108070` | RESET | Réinitialiser l'appareil | Remet les paramètres par défaut |
| `0x108090` | REBOOT | Redémarrer l'appareil | Redémarre le terminal |
| `0x1080B0` | SLEEP | Mettre en veille | Place le terminal en mode veille |
| `0x100010` | STATUS | Demander le statut | Demande les infos de l'appareil |

---

## Endpoints API disponibles

### Base URL
```
/api/v1/devices
```

### Permission requise
Tous les endpoints de commande nécessitent la permission `device:command`.

### Endpoints

#### 1. Envoyer une commande générique
```http
POST /api/v1/devices/{device_id}/command
Content-Type: application/json
Authorization: Bearer {token}

{
  "command": "reboot"  // "reset" | "reboot" | "sleep" | "status"
}
```

**Réponse :**
```json
{
  "success": true,
  "device_id": "uuid-device-123",
  "device_serial": "SN-DEVICE-001",
  "command": "reboot",
  "command_code": "0x108090",
  "message": "Commande REBOOT envoyée au terminal SN-DEVICE-001"
}
```

#### 2. Raccourcis de commandes

```http
POST /api/v1/devices/{device_id}/reboot    # Redémarrer
POST /api/v1/devices/{device_id}/reset     # Réinitialiser
POST /api/v1/devices/{device_id}/sleep     # Mettre en veille
POST /api/v1/devices/{device_id}/status    # Demander statut
```

Ces endpoints ne nécessitent pas de body.

#### 3. Commande groupée (bulk)

```http
POST /api/v1/devices/bulk/command
Content-Type: application/json
Authorization: Bearer {token}

{
  "device_ids": ["uuid-device-1", "uuid-device-2", "uuid-device-3"],
  "command": "status"
}
```

**Réponse :**
```json
{
  "success": true,
  "total_devices": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "success": true,
      "device_id": "uuid-device-1",
      "device_serial": "SN-001",
      "command": "status",
      "command_code": "0x100010",
      "message": "Commande STATUS envoyée"
    },
    // ...
  ]
}
```

#### 4. Vérifier le statut MQTT

```http
GET /api/v1/devices/mqtt/status
Authorization: Bearer {token}
```

**Réponse :**
```json
{
  "connected": true,
  "broker_host": "mqtt.example.com",
  "broker_port": 8883
}
```

---

## Statut des terminaux (Heartbeat)

Le backend détecte automatiquement si un terminal est **online** ou **offline** grâce à un système de heartbeat MQTT.

### Comment ça fonctionne

```
┌─────────────┐     Heartbeat (toutes les X min)      ┌──────────────┐
│  Terminal   │ ─────────────────────────────────────► │   Backend    │
│    IoT      │   Topic: kuilinga/devices/{serial}/status │   (FastAPI)  │
└─────────────┘                                        └──────────────┘
                                                              │
                                                              ▼
                                                    ┌──────────────────┐
                                                    │ Met à jour en BDD │
                                                    │ - status = ONLINE │
                                                    │ - last_seen_at    │
                                                    │ - battery_level   │
                                                    │ - wifi_rssi       │
                                                    └──────────────────┘
```

1. **Réception du heartbeat** : Le terminal envoie périodiquement un message sur `kuilinga/devices/{serial}/status`
2. **Mise à jour en BDD** : Le backend met à jour `status=ONLINE` et `last_seen_at`
3. **Détection offline** : Un job planifié vérifie toutes les 60 secondes si un terminal n'a pas envoyé de heartbeat depuis 5 minutes → le marque `OFFLINE`

### Format du message Heartbeat (MQTT)

**Topic**: `kuilinga/devices/{serial_number}/status`

**Payload** (JSON):
```json
{
  "status": "online",
  "firmware_version": "2.1.0",
  "battery_level": 85,
  "wifi_rssi": -45,
  "timestamp": "2024-01-15T10:05:00Z"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `status` | string | Toujours "online" pour un heartbeat |
| `firmware_version` | string | Version du firmware (ex: "2.1.0") |
| `battery_level` | integer | Niveau de batterie 0-100% |
| `wifi_rssi` | integer | Force du signal WiFi en dBm (ex: -45) |
| `timestamp` | string | Horodatage ISO 8601 |

### Nouveaux champs dans la réponse API Device

L'endpoint `GET /api/v1/devices` et `GET /api/v1/devices/{id}` retournent maintenant ces champs supplémentaires :

```json
{
  "id": "uuid-device-123",
  "serial_number": "SN-DEVICE-001",
  "type": "Terminal Fixe",
  "status": "online",
  "delivery_method": "mqtt",
  "organization": { "id": "...", "name": "ACME Corp" },
  "site": { "id": "...", "name": "Siège" },

  "last_attendance_timestamp": "2024-01-15T14:30:00Z",
  "daily_attendance_count": 42,

  "last_seen_at": "2024-01-15T14:35:00Z",
  "firmware_version": "2.1.0",
  "battery_level": 85,
  "wifi_rssi": -45
}
```

| Nouveau champ | Type | Description |
|---------------|------|-------------|
| `last_seen_at` | datetime \| null | Dernière communication reçue (heartbeat ou pointage) |
| `firmware_version` | string \| null | Version du firmware |
| `battery_level` | integer \| null | Niveau de batterie (0-100%) |
| `wifi_rssi` | integer \| null | Force du signal WiFi en dBm |

### Configuration Backend

Les paramètres de détection sont configurables via `.env` :

```env
# Intervalle de vérification (en secondes)
DEVICE_STATUS_CHECK_INTERVAL_SECONDS=60

# Délai sans heartbeat avant de marquer OFFLINE (en minutes)
DEVICE_OFFLINE_TIMEOUT_MINUTES=5
```

### Valeurs de statut

| Statut | Description | Couleur suggérée |
|--------|-------------|------------------|
| `online` | Terminal connecté, heartbeat récent | 🟢 Vert |
| `offline` | Pas de heartbeat depuis > 5 minutes | 🔴 Rouge |
| `maintenance` | En maintenance (défini manuellement) | 🟡 Jaune |

### Implémentation Frontend - Interface TypeScript

```typescript
// types/device.ts

export type DeviceStatus = 'online' | 'offline' | 'maintenance';
export type DeliveryMethod = 'http' | 'mqtt';

export interface Device {
  id: string;
  serial_number: string;
  type: string;
  status: DeviceStatus;
  delivery_method: DeliveryMethod;

  organization?: {
    id: string;
    name: string;
  };
  site?: {
    id: string;
    name: string;
  };

  // Statistiques de pointage
  last_attendance_timestamp?: string;
  daily_attendance_count: number;

  // Heartbeat / monitoring (NOUVEAUX)
  last_seen_at?: string;
  firmware_version?: string;
  battery_level?: number;  // 0-100
  wifi_rssi?: number;      // dBm, toujours négatif (ex: -45)
}
```

### Implémentation Frontend - Composant de statut

```tsx
// components/DeviceStatusBadge.tsx

import React from 'react';
import { Chip, Tooltip, Stack, Typography } from '@mui/material';
import {
  Wifi,
  WifiOff,
  Battery20,
  Battery50,
  Battery80,
  BatteryFull,
  SignalCellular4Bar,
  SignalCellular2Bar,
  SignalCellular0Bar,
} from '@mui/icons-material';
import { Device, DeviceStatus } from '../types/device';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

interface DeviceStatusBadgeProps {
  device: Device;
  showDetails?: boolean;
}

export const DeviceStatusBadge: React.FC<DeviceStatusBadgeProps> = ({
  device,
  showDetails = false,
}) => {
  const getStatusColor = (status: DeviceStatus) => {
    switch (status) {
      case 'online': return 'success';
      case 'offline': return 'error';
      case 'maintenance': return 'warning';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: DeviceStatus) => {
    switch (status) {
      case 'online': return 'En ligne';
      case 'offline': return 'Hors ligne';
      case 'maintenance': return 'Maintenance';
      default: return status;
    }
  };

  const getBatteryIcon = (level?: number) => {
    if (level === undefined || level === null) return null;
    if (level >= 80) return <BatteryFull color="success" fontSize="small" />;
    if (level >= 50) return <Battery80 color="success" fontSize="small" />;
    if (level >= 20) return <Battery50 color="warning" fontSize="small" />;
    return <Battery20 color="error" fontSize="small" />;
  };

  const getSignalIcon = (rssi?: number) => {
    if (rssi === undefined || rssi === null) return null;
    // RSSI: -30 excellent, -50 bon, -70 faible, -90 très faible
    if (rssi >= -50) return <SignalCellular4Bar color="success" fontSize="small" />;
    if (rssi >= -70) return <SignalCellular2Bar color="warning" fontSize="small" />;
    return <SignalCellular0Bar color="error" fontSize="small" />;
  };

  const getLastSeenText = () => {
    if (!device.last_seen_at) return 'Jamais vu';
    return `Vu ${formatDistanceToNow(new Date(device.last_seen_at), {
      addSuffix: true,
      locale: fr,
    })}`;
  };

  const tooltipContent = (
    <Stack spacing={0.5}>
      <Typography variant="caption">
        {getLastSeenText()}
      </Typography>
      {device.firmware_version && (
        <Typography variant="caption">
          Firmware: {device.firmware_version}
        </Typography>
      )}
      {device.battery_level !== undefined && device.battery_level !== null && (
        <Typography variant="caption">
          Batterie: {device.battery_level}%
        </Typography>
      )}
      {device.wifi_rssi !== undefined && device.wifi_rssi !== null && (
        <Typography variant="caption">
          Signal WiFi: {device.wifi_rssi} dBm
        </Typography>
      )}
    </Stack>
  );

  return (
    <Tooltip title={tooltipContent} arrow>
      <Stack direction="row" spacing={1} alignItems="center">
        <Chip
          icon={device.status === 'online' ? <Wifi /> : <WifiOff />}
          label={getStatusLabel(device.status)}
          color={getStatusColor(device.status)}
          size="small"
          variant="outlined"
        />

        {showDetails && device.status === 'online' && (
          <>
            {getBatteryIcon(device.battery_level)}
            {getSignalIcon(device.wifi_rssi)}
          </>
        )}
      </Stack>
    </Tooltip>
  );
};
```

### Implémentation Frontend - Tableau des terminaux avec statut

```tsx
// components/DeviceTable.tsx

import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
} from '@mui/material';
import { Device } from '../types/device';
import { DeviceStatusBadge } from './DeviceStatusBadge';
import { DeviceActions } from './DeviceActions';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

interface DeviceTableProps {
  devices: Device[];
  onRefresh: () => void;
}

export const DeviceTable: React.FC<DeviceTableProps> = ({ devices, onRefresh }) => {
  const formatLastSeen = (lastSeenAt?: string) => {
    if (!lastSeenAt) return '-';
    return formatDistanceToNow(new Date(lastSeenAt), {
      addSuffix: true,
      locale: fr,
    });
  };

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>N° Série</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Site</TableCell>
            <TableCell>Statut</TableCell>
            <TableCell>Dernière activité</TableCell>
            <TableCell>Firmware</TableCell>
            <TableCell>Batterie</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {devices.map((device) => (
            <TableRow
              key={device.id}
              sx={{
                backgroundColor: device.status === 'offline' ? 'rgba(255, 0, 0, 0.05)' : 'inherit',
              }}
            >
              <TableCell>
                <Typography variant="body2" fontWeight="medium">
                  {device.serial_number}
                </Typography>
              </TableCell>
              <TableCell>{device.type}</TableCell>
              <TableCell>{device.site?.name || '-'}</TableCell>
              <TableCell>
                <DeviceStatusBadge device={device} showDetails />
              </TableCell>
              <TableCell>
                <Typography
                  variant="body2"
                  color={device.last_seen_at ? 'text.primary' : 'text.secondary'}
                >
                  {formatLastSeen(device.last_seen_at)}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography variant="body2" color="text.secondary">
                  {device.firmware_version || '-'}
                </Typography>
              </TableCell>
              <TableCell>
                {device.battery_level !== undefined && device.battery_level !== null ? (
                  <Typography
                    variant="body2"
                    color={
                      device.battery_level < 20 ? 'error' :
                      device.battery_level < 50 ? 'warning.main' : 'text.primary'
                    }
                  >
                    {device.battery_level}%
                  </Typography>
                ) : (
                  '-'
                )}
              </TableCell>
              <TableCell>
                <DeviceActions
                  deviceId={device.id}
                  deviceSerial={device.serial_number}
                  onCommandSuccess={onRefresh}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};
```

### Implémentation Frontend - Hook de polling pour rafraîchir le statut

```typescript
// hooks/useDevicePolling.ts

import { useEffect, useCallback, useRef } from 'react';

interface UseDevicePollingOptions {
  enabled?: boolean;
  intervalMs?: number;
}

export const useDevicePolling = (
  fetchDevices: () => Promise<void>,
  options: UseDevicePollingOptions = {}
) => {
  const { enabled = true, intervalMs = 30000 } = options;
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const startPolling = useCallback(() => {
    if (intervalRef.current) return;

    intervalRef.current = setInterval(() => {
      fetchDevices();
    }, intervalMs);
  }, [fetchDevices, intervalMs]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (enabled) {
      fetchDevices(); // Fetch initial
      startPolling();
    } else {
      stopPolling();
    }

    return () => stopPolling();
  }, [enabled, startPolling, stopPolling, fetchDevices]);

  return { startPolling, stopPolling };
};
```

### Implémentation Frontend - Page complète

```tsx
// pages/DevicesPage.tsx

import React, { useState, useCallback } from 'react';
import { Box, Typography, Alert, LinearProgress, Button } from '@mui/material';
import { Refresh } from '@mui/icons-material';
import { DeviceTable } from '../components/DeviceTable';
import { MqttStatusIndicator } from '../components/MqttStatusIndicator';
import { useDevicePolling } from '../hooks/useDevicePolling';
import { api } from '../services/api';
import { Device } from '../types/device';

export const DevicesPage: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDevices = useCallback(async () => {
    try {
      setError(null);
      const response = await api.get('/devices');
      setDevices(response.data.items);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement');
    } finally {
      setLoading(false);
    }
  }, []);

  // Rafraîchissement automatique toutes les 30 secondes
  useDevicePolling(fetchDevices, { intervalMs: 30000 });

  const onlineCount = devices.filter(d => d.status === 'online').length;
  const offlineCount = devices.filter(d => d.status === 'offline').length;

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Terminaux IoT
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {onlineCount} en ligne • {offlineCount} hors ligne
          </Typography>
        </Box>
        <Box display="flex" gap={2} alignItems="center">
          <MqttStatusIndicator />
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchDevices}
            disabled={loading}
          >
            Actualiser
          </Button>
        </Box>
      </Box>

      {/* Loading */}
      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Alerte si beaucoup de terminaux offline */}
      {offlineCount > devices.length / 2 && devices.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Attention : Plus de la moitié des terminaux sont hors ligne.
          Vérifiez la connexion réseau ou le broker MQTT.
        </Alert>
      )}

      {/* Table */}
      <DeviceTable devices={devices} onRefresh={fetchDevices} />
    </Box>
  );
};
```

### Résumé pour le Frontend

| Tâche | Description |
|-------|-------------|
| **Afficher le statut** | Utiliser le champ `status` (`online`, `offline`, `maintenance`) |
| **Afficher la dernière activité** | Utiliser `last_seen_at` avec une lib comme `date-fns` |
| **Afficher les métadonnées** | `firmware_version`, `battery_level`, `wifi_rssi` |
| **Polling automatique** | Rafraîchir la liste toutes les 30 secondes |
| **Indicateurs visuels** | Icônes de batterie/signal selon les seuils |

Le statut est **automatiquement géré par le backend**. Le frontend n'a qu'à :
1. Lire les champs retournés par l'API
2. Afficher les informations de manière visuelle
3. Rafraîchir périodiquement pour voir les changements de statut

---

## Implémentation Frontend

### 1. Service API TypeScript

```typescript
// services/deviceCommandService.ts

import { api } from './api';

export type DeviceCommand = 'reset' | 'reboot' | 'sleep' | 'status';

export interface CommandResponse {
  success: boolean;
  device_id: string;
  device_serial: string;
  command: string;
  command_code: string;
  message: string;
}

export interface BulkCommandResponse {
  success: boolean;
  total_devices: number;
  successful: number;
  failed: number;
  results: CommandResponse[];
}

export interface MqttStatus {
  connected: boolean;
  broker_host: string | null;
  broker_port: number | null;
}

// Codes hexadécimaux pour référence
export const DEVICE_COMMAND_CODES = {
  ACCEPTED: '0x001020',
  REFUSED: '0x003020',
  RESET: '0x108070',
  REJECTED: '0x108080',
  REBOOT: '0x108090',
  SLEEP: '0x1080B0',
  STATUS: '0x100010',
} as const;

export const deviceCommandService = {
  // Envoyer une commande générique
  async sendCommand(deviceId: string, command: DeviceCommand): Promise<CommandResponse> {
    const response = await api.post(`/devices/${deviceId}/command`, { command });
    return response.data;
  },

  // Raccourcis de commandes
  async rebootDevice(deviceId: string): Promise<CommandResponse> {
    const response = await api.post(`/devices/${deviceId}/reboot`);
    return response.data;
  },

  async resetDevice(deviceId: string): Promise<CommandResponse> {
    const response = await api.post(`/devices/${deviceId}/reset`);
    return response.data;
  },

  async sleepDevice(deviceId: string): Promise<CommandResponse> {
    const response = await api.post(`/devices/${deviceId}/sleep`);
    return response.data;
  },

  async requestStatus(deviceId: string): Promise<CommandResponse> {
    const response = await api.post(`/devices/${deviceId}/status`);
    return response.data;
  },

  // Commande groupée
  async sendBulkCommand(deviceIds: string[], command: DeviceCommand): Promise<BulkCommandResponse> {
    const response = await api.post('/devices/bulk/command', {
      device_ids: deviceIds,
      command,
    });
    return response.data;
  },

  // Vérifier statut MQTT
  async getMqttStatus(): Promise<MqttStatus> {
    const response = await api.get('/devices/mqtt/status');
    return response.data;
  },
};
```

### 2. Composant React - Actions sur un terminal

```tsx
// components/DeviceActions.tsx

import React, { useState } from 'react';
import {
  Button,
  Menu,
  MenuItem,
  CircularProgress,
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  MoreVert,
  Refresh,
  RestartAlt,
  PowerSettingsNew,
  Info
} from '@mui/icons-material';
import { deviceCommandService, DeviceCommand } from '../services/deviceCommandService';

interface DeviceActionsProps {
  deviceId: string;
  deviceSerial: string;
  onCommandSuccess?: () => void;
}

export const DeviceActions: React.FC<DeviceActionsProps> = ({
  deviceId,
  deviceSerial,
  onCommandSuccess
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [loading, setLoading] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState<DeviceCommand | null>(null);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({ open: false, message: '', severity: 'success' });

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleCommandClick = (command: DeviceCommand) => {
    handleMenuClose();
    // Demander confirmation pour les commandes critiques
    if (['reset', 'reboot', 'sleep'].includes(command)) {
      setConfirmDialog(command);
    } else {
      executeCommand(command);
    }
  };

  const executeCommand = async (command: DeviceCommand) => {
    setLoading(true);
    setConfirmDialog(null);

    try {
      const response = await deviceCommandService.sendCommand(deviceId, command);

      setSnackbar({
        open: true,
        message: response.message,
        severity: 'success',
      });

      onCommandSuccess?.();
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Erreur lors de l\'envoi de la commande';
      setSnackbar({
        open: true,
        message: errorMessage,
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const getCommandLabel = (command: DeviceCommand): string => {
    const labels: Record<DeviceCommand, string> = {
      reset: 'Réinitialiser',
      reboot: 'Redémarrer',
      sleep: 'Mettre en veille',
      status: 'Demander statut',
    };
    return labels[command];
  };

  const getCommandIcon = (command: DeviceCommand) => {
    const icons: Record<DeviceCommand, React.ReactNode> = {
      reset: <RestartAlt fontSize="small" />,
      reboot: <Refresh fontSize="small" />,
      sleep: <PowerSettingsNew fontSize="small" />,
      status: <Info fontSize="small" />,
    };
    return icons[command];
  };

  return (
    <>
      <Button
        variant="outlined"
        size="small"
        onClick={handleMenuOpen}
        disabled={loading}
        startIcon={loading ? <CircularProgress size={16} /> : <MoreVert />}
      >
        Actions
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        {(['status', 'reboot', 'reset', 'sleep'] as DeviceCommand[]).map((command) => (
          <MenuItem
            key={command}
            onClick={() => handleCommandClick(command)}
          >
            {getCommandIcon(command)}
            <span style={{ marginLeft: 8 }}>{getCommandLabel(command)}</span>
          </MenuItem>
        ))}
      </Menu>

      {/* Dialog de confirmation */}
      <Dialog open={confirmDialog !== null} onClose={() => setConfirmDialog(null)}>
        <DialogTitle>Confirmer l'action</DialogTitle>
        <DialogContent>
          Êtes-vous sûr de vouloir {confirmDialog && getCommandLabel(confirmDialog).toLowerCase()}
          le terminal <strong>{deviceSerial}</strong> ?
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog(null)}>Annuler</Button>
          <Button
            onClick={() => confirmDialog && executeCommand(confirmDialog)}
            variant="contained"
            color="primary"
          >
            Confirmer
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar de notification */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
};
```

### 3. Composant - Actions groupées

```tsx
// components/BulkDeviceActions.tsx

import React, { useState } from 'react';
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import { Check, Close } from '@mui/icons-material';
import { deviceCommandService, DeviceCommand, BulkCommandResponse } from '../services/deviceCommandService';

interface BulkDeviceActionsProps {
  selectedDeviceIds: string[];
  onComplete?: () => void;
}

export const BulkDeviceActions: React.FC<BulkDeviceActionsProps> = ({
  selectedDeviceIds,
  onComplete,
}) => {
  const [open, setOpen] = useState(false);
  const [command, setCommand] = useState<DeviceCommand>('status');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BulkCommandResponse | null>(null);

  const handleExecute = async () => {
    setLoading(true);
    setResult(null);

    try {
      const response = await deviceCommandService.sendBulkCommand(selectedDeviceIds, command);
      setResult(response);
      onComplete?.();
    } catch (error: any) {
      setResult({
        success: false,
        total_devices: selectedDeviceIds.length,
        successful: 0,
        failed: selectedDeviceIds.length,
        results: [],
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setOpen(false);
    setResult(null);
  };

  return (
    <>
      <Button
        variant="contained"
        onClick={() => setOpen(true)}
        disabled={selectedDeviceIds.length === 0}
      >
        Actions groupées ({selectedDeviceIds.length})
      </Button>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>Actions groupées sur {selectedDeviceIds.length} terminaux</DialogTitle>
        <DialogContent>
          {!result ? (
            <>
              <FormControl fullWidth sx={{ mt: 2 }}>
                <InputLabel>Commande</InputLabel>
                <Select
                  value={command}
                  label="Commande"
                  onChange={(e) => setCommand(e.target.value as DeviceCommand)}
                  disabled={loading}
                >
                  <MenuItem value="status">Demander statut (0x100010)</MenuItem>
                  <MenuItem value="reboot">Redémarrer (0x108090)</MenuItem>
                  <MenuItem value="reset">Réinitialiser (0x108070)</MenuItem>
                  <MenuItem value="sleep">Mettre en veille (0x1080B0)</MenuItem>
                </Select>
              </FormControl>
              {loading && <LinearProgress sx={{ mt: 2 }} />}
            </>
          ) : (
            <>
              <Alert
                severity={result.success ? 'success' : result.successful > 0 ? 'warning' : 'error'}
                sx={{ mb: 2 }}
              >
                {result.successful} / {result.total_devices} commandes envoyées avec succès
              </Alert>
              <List dense>
                {result.results.map((r, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      {r.success ? <Check color="success" /> : <Close color="error" />}
                    </ListItemIcon>
                    <ListItemText
                      primary={r.device_serial}
                      secondary={r.message}
                    />
                  </ListItem>
                ))}
              </List>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>
            {result ? 'Fermer' : 'Annuler'}
          </Button>
          {!result && (
            <Button
              onClick={handleExecute}
              variant="contained"
              disabled={loading}
            >
              Exécuter
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </>
  );
};
```

### 4. Indicateur de statut MQTT

```tsx
// components/MqttStatusIndicator.tsx

import React, { useEffect, useState } from 'react';
import { Chip, Tooltip } from '@mui/material';
import { Wifi, WifiOff } from '@mui/icons-material';
import { deviceCommandService, MqttStatus } from '../services/deviceCommandService';

export const MqttStatusIndicator: React.FC = () => {
  const [status, setStatus] = useState<MqttStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const mqttStatus = await deviceCommandService.getMqttStatus();
        setStatus(mqttStatus);
      } catch (error) {
        setStatus({ connected: false, broker_host: null, broker_port: null });
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    // Rafraîchir toutes les 30 secondes
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <Chip label="MQTT..." size="small" />;
  }

  return (
    <Tooltip
      title={
        status?.connected
          ? `Connecté à ${status.broker_host}:${status.broker_port}`
          : 'Déconnecté du broker MQTT'
      }
    >
      <Chip
        icon={status?.connected ? <Wifi /> : <WifiOff />}
        label={status?.connected ? 'MQTT Connecté' : 'MQTT Déconnecté'}
        color={status?.connected ? 'success' : 'error'}
        size="small"
        variant="outlined"
      />
    </Tooltip>
  );
};
```

---

## Gestion des WebSockets

Le backend envoie des événements en temps réel via WebSocket pour notifier le frontend des pointages et réponses.

### Connexion WebSocket

```typescript
// hooks/useWebSocket.ts

import { useEffect, useRef, useCallback, useState } from 'react';

interface AttendanceEvent {
  type: 'new_attendance';
  payload: {
    id: string;
    employee_id: string;
    device_id: string;
    timestamp: string;
    type: 'in' | 'out';
    // ... autres champs
  };
}

export const useAttendanceWebSocket = (onNewAttendance: (event: AttendanceEvent) => void) => {
  const ws = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);

  const connect = useCallback(() => {
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws`;

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WebSocket connecté');
      setConnected(true);
    };

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'new_attendance') {
          onNewAttendance(data);
        }
      } catch (error) {
        console.error('Erreur parsing WebSocket:', error);
      }
    };

    ws.current.onclose = () => {
      console.log('WebSocket déconnecté');
      setConnected(false);
      // Reconnexion automatique après 5s
      setTimeout(connect, 5000);
    };

    ws.current.onerror = (error) => {
      console.error('Erreur WebSocket:', error);
    };
  }, [onNewAttendance]);

  useEffect(() => {
    connect();
    return () => ws.current?.close();
  }, [connect]);

  return { connected };
};
```

### Utilisation dans un composant

```tsx
// pages/DevicesPage.tsx

import React, { useState, useCallback } from 'react';
import { useAttendanceWebSocket } from '../hooks/useWebSocket';

export const DevicesPage: React.FC = () => {
  const [recentAttendances, setRecentAttendances] = useState<any[]>([]);

  const handleNewAttendance = useCallback((event: any) => {
    // Ajouter le nouveau pointage en haut de la liste
    setRecentAttendances(prev => [event.payload, ...prev.slice(0, 9)]);

    // Optionnel: notification toast
    // toast.success(`Pointage enregistré: ${event.payload.employee_name}`);
  }, []);

  const { connected } = useAttendanceWebSocket(handleNewAttendance);

  return (
    <div>
      {/* Indicateur de connexion WebSocket */}
      <div style={{ marginBottom: 16 }}>
        Status WebSocket: {connected ? '🟢 Connecté' : '🔴 Déconnecté'}
      </div>

      {/* Liste des pointages récents en temps réel */}
      <h3>Pointages récents</h3>
      <ul>
        {recentAttendances.map((attendance, i) => (
          <li key={i}>
            {attendance.timestamp} - {attendance.type}
          </li>
        ))}
      </ul>
    </div>
  );
};
```

---

## Configuration SSL/TLS

Pour la connexion sécurisée aux appareils IoT via MQTT, le backend utilise des certificats SSL/TLS.

### Variables d'environnement

```env
# Activer TLS
MQTT_TLS_ENABLED=True

# Chemin vers le certificat CA (autorité de certification)
MQTT_CA_CERT=certs/ca.crt

# Certificat client (optionnel, pour authentification mutuelle)
MQTT_CLIENT_CERT=certs/client.crt
MQTT_CLIENT_KEY=certs/client.key

# Mode développement uniquement (désactive vérification hostname)
MQTT_TLS_INSECURE=False
```

### Procédure pour générer les certificats

Le fournisseur des appareils IoT devrait vous fournir :
1. **ca.crt** : Certificat de l'autorité de certification
2. **client.crt** : Certificat client (si authentification mutuelle requise)
3. **client.key** : Clé privée du certificat client

Placez ces fichiers dans le dossier `certs/` à la racine du projet.

---

## Exemples de code

### Page complète de gestion des terminaux

```tsx
// pages/DeviceManagement.tsx

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  TableContainer,
  Checkbox,
  Typography,
  Toolbar,
} from '@mui/material';
import { DeviceActions } from '../components/DeviceActions';
import { BulkDeviceActions } from '../components/BulkDeviceActions';
import { MqttStatusIndicator } from '../components/MqttStatusIndicator';
import { useAttendanceWebSocket } from '../hooks/useWebSocket';
import { api } from '../services/api';

interface Device {
  id: string;
  serial_number: string;
  type: string;
  status: 'online' | 'offline' | 'maintenance';
  site?: { name: string };
}

export const DeviceManagement: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  // WebSocket pour les mises à jour en temps réel
  useAttendanceWebSocket((event) => {
    console.log('Nouveau pointage:', event);
  });

  // Charger les terminaux
  const fetchDevices = async () => {
    try {
      const response = await api.get('/devices');
      setDevices(response.data.items);
    } catch (error) {
      console.error('Erreur chargement terminaux:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const handleSelectAll = (checked: boolean) => {
    setSelectedIds(checked ? devices.map(d => d.id) : []);
  };

  const handleSelectOne = (id: string, checked: boolean) => {
    setSelectedIds(prev =>
      checked ? [...prev, id] : prev.filter(i => i !== id)
    );
  };

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Gestion des Terminaux</Typography>
        <MqttStatusIndicator />
      </Box>

      <Toolbar sx={{ pl: 0 }}>
        <BulkDeviceActions
          selectedDeviceIds={selectedIds}
          onComplete={fetchDevices}
        />
      </Toolbar>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={selectedIds.length > 0 && selectedIds.length < devices.length}
                  checked={devices.length > 0 && selectedIds.length === devices.length}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                />
              </TableCell>
              <TableCell>Numéro de série</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Site</TableCell>
              <TableCell>Statut</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {devices.map((device) => (
              <TableRow key={device.id} hover>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selectedIds.includes(device.id)}
                    onChange={(e) => handleSelectOne(device.id, e.target.checked)}
                  />
                </TableCell>
                <TableCell>{device.serial_number}</TableCell>
                <TableCell>{device.type}</TableCell>
                <TableCell>{device.site?.name || '-'}</TableCell>
                <TableCell>
                  <Chip
                    label={device.status}
                    color={device.status === 'online' ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <DeviceActions
                    deviceId={device.id}
                    deviceSerial={device.serial_number}
                    onCommandSuccess={fetchDevices}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};
```

---

## Codes d'erreur HTTP

| Code | Signification |
|------|---------------|
| 200 | Commande envoyée avec succès |
| 401 | Non authentifié |
| 403 | Permission insuffisante (nécessite `device:command`) |
| 404 | Terminal non trouvé |
| 500 | Erreur interne (échec envoi MQTT) |
| 503 | Service MQTT non disponible |

---

## Checklist d'implémentation

- [ ] Créer le service `deviceCommandService.ts`
- [ ] Implémenter le composant `DeviceActions` pour les actions individuelles
- [ ] Implémenter le composant `BulkDeviceActions` pour les actions groupées
- [ ] Ajouter l'indicateur `MqttStatusIndicator`
- [ ] Intégrer le WebSocket pour les notifications temps réel
- [ ] Ajouter les boutons d'action dans la page de gestion des terminaux
- [ ] Gérer les erreurs et afficher les notifications appropriées
- [ ] Ajouter les confirmations pour les actions critiques (reset, reboot, sleep)
- [ ] Tester avec le swagger à `http://localhost:8000/docs`

---

## Questions fréquentes

### Comment savoir si un terminal a reçu la commande ?

Le backend envoie la commande via MQTT mais ne reçoit pas de confirmation directe. Le terminal devrait répondre sur le topic `kuilinga/devices/{serial}/status` que le backend écoute. Ces réponses peuvent être diffusées via WebSocket.

### Que se passe-t-il si le broker MQTT est déconnecté ?

L'endpoint retournera une erreur 503 (Service Unavailable). Le frontend devrait afficher un message approprié et permettre de réessayer plus tard.

### Comment tester sans appareil IoT réel ?

Utilisez un client MQTT comme MQTT Explorer ou mosquitto_pub/sub pour simuler un terminal :

```bash
# Simuler un pointage
mosquitto_pub -h localhost -t "kuilinga/devices/SN-TEST-001/attendance" \
  -m '{"badge_id": "BADGE-123", "type": "in", "timestamp": "2024-01-15T08:00:00Z"}'

# Écouter les commandes
mosquitto_sub -h localhost -t "kuilinga/devices/SN-TEST-001/command" -v
```
