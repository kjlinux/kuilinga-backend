# Guide d'Intégration Frontend - Logout avec Invalidation des Tokens

## Vue d'ensemble

Ce guide explique comment intégrer la fonctionnalité de logout côté frontend pour communiquer avec le backend Kuilinga.

## Endpoint de Logout

### URL
```
POST /api/v1/auth/logout
```

### Headers Requis
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Body (Optionnel mais Recommandé)
```json
{
  "refresh_token": "votre_refresh_token_ici"
}
```

**Note:** Le refresh_token est optionnel mais fortement recommandé pour invalider complètement la session utilisateur.

## Implémentation Frontend

### 1. Fonction de Logout (JavaScript/TypeScript)

```typescript
async function logout() {
  const accessToken = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');

  try {
    // Appeler l'endpoint de logout
    const response = await fetch('http://localhost:8000/api/v1/auth/logout', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: refreshToken
      })
    });

    const data = await response.json();

    if (response.ok) {
      console.log('Logout réussi:', data);
      // data.access_token_revoked: true
      // data.refresh_token_revoked: true
    } else {
      console.warn('Erreur lors du logout côté serveur:', data);
      // Continuer quand même avec le nettoyage local
    }

  } catch (error) {
    console.error('Erreur réseau lors du logout:', error);
    // Continuer quand même avec le nettoyage local
  } finally {
    // IMPORTANT: Toujours nettoyer les tokens locaux,
    // même si le backend échoue
    cleanupLocalTokens();
    redirectToLogin();
  }
}

function cleanupLocalTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  // Nettoyer tout autre état d'authentification
}

function redirectToLogin() {
  window.location.href = '/login';
}
```

### 2. Exemple avec Axios

```typescript
import axios from 'axios';

async function logout() {
  const accessToken = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');

  try {
    const response = await axios.post(
      'http://localhost:8000/api/v1/auth/logout',
      { refresh_token: refreshToken },
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      }
    );

    console.log('Logout réussi:', response.data);

  } catch (error) {
    if (error.response) {
      // Le serveur a répondu avec un code d'erreur
      console.error('Erreur serveur:', error.response.status, error.response.data);
    } else if (error.request) {
      // La requête a été faite mais pas de réponse
      console.error('Pas de réponse du serveur:', error.request);
    } else {
      // Erreur lors de la configuration de la requête
      console.error('Erreur:', error.message);
    }
  } finally {
    // Toujours nettoyer localement
    cleanupLocalTokens();
    redirectToLogin();
  }
}
```

### 3. Exemple avec React + Context API

```typescript
// AuthContext.tsx
import React, { createContext, useContext, useState } from 'react';

interface AuthContextType {
  user: User | null;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const logout = async () => {
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');

    try {
      await fetch('http://localhost:8000/api/v1/auth/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken })
      });
    } catch (error) {
      console.error('Erreur lors du logout:', error);
      // Continuer quand même
    } finally {
      // Nettoyer l'état local
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);

      // Rediriger vers login
      window.location.href = '/login';
    }
  };

  return (
    <AuthContext.Provider value={{ user, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Utilisation dans un composant
function LogoutButton() {
  const { logout } = useAuth();

  return (
    <button onClick={logout}>
      Se déconnecter
    </button>
  );
}
```

### 4. Exemple avec Vue 3 + Composition API

```typescript
// useAuth.ts
import { ref } from 'vue';
import { useRouter } from 'vue-router';

export function useAuth() {
  const user = ref(null);
  const router = useRouter();

  const logout = async () => {
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');

    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken })
      });

      if (response.ok) {
        console.log('Logout réussi');
      }
    } catch (error) {
      console.error('Erreur lors du logout:', error);
    } finally {
      // Nettoyer l'état
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      user.value = null;

      // Rediriger
      router.push('/login');
    }
  };

  return { user, logout };
}

// Utilisation dans un composant Vue
<template>
  <button @click="logout">Se déconnecter</button>
</template>

<script setup>
import { useAuth } from '@/composables/useAuth';

const { logout } = useAuth();
</script>
```

## Gestion des Erreurs

### Réponses Possibles

#### Succès (200 OK)
```json
{
  "message": "Déconnexion réussie",
  "access_token_revoked": true,
  "refresh_token_revoked": true
}
```

#### Succès Partiel (200 OK)
Si le serveur a un problème mais veut quand même permettre le logout local:
```json
{
  "message": "Déconnexion réussie (locale uniquement)",
  "warning": "Les tokens n'ont pas pu être invalidés côté serveur"
}
```

#### Token Invalide (401 Unauthorized)
```json
{
  "detail": "Could not validate credentials"
}
```

#### Token Manquant (401 Unauthorized)
```json
{
  "detail": "Not authenticated"
}
```

### Stratégie Recommandée

**IMPORTANT:** Toujours nettoyer les tokens locaux, même si l'appel API échoue!

```typescript
async function logout() {
  // 1. Essayer d'invalider côté serveur
  try {
    await callLogoutAPI();
  } catch (error) {
    // Ne pas bloquer si le serveur échoue
    console.warn('Logout serveur échoué, nettoyage local seulement');
  }

  // 2. TOUJOURS nettoyer localement
  cleanupLocalTokens();

  // 3. TOUJOURS rediriger
  redirectToLogin();
}
```

## Intercepteurs HTTP (Recommandé)

### Intercepteur Axios pour Gérer les Tokens Révoqués

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

// Intercepteur de réponse
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Si token révoqué (403)
    if (error.response?.status === 403) {
      const detail = error.response.data?.detail;

      if (detail === 'Could not validate credentials') {
        // Token révoqué ou invalide
        console.warn('Token révoqué détecté, déconnexion...');
        cleanupLocalTokens();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

## Scénarios Spéciaux

### 1. Logout de Tous les Appareils (Future Feature)

Pour l'instant, le logout ne révoque que les tokens fournis. Si l'utilisateur a plusieurs sessions (plusieurs appareils), chaque appareil doit appeler logout individuellement.

**Amélioration future:** Un endpoint `/auth/logout-all` pourrait révoquer tous les tokens de l'utilisateur.

### 2. Token Expiré au Moment du Logout

Si le token est déjà expiré quand l'utilisateur clique sur "Se déconnecter":

```typescript
async function logout() {
  const accessToken = localStorage.getItem('access_token');

  if (!accessToken) {
    // Pas de token, juste nettoyer et rediriger
    cleanupLocalTokens();
    redirectToLogin();
    return;
  }

  try {
    // Essayer quand même l'appel API
    await callLogoutAPI();
  } catch (error) {
    // Si 401/403, c'est OK - le token était déjà invalide
    if (error.response?.status === 401 || error.response?.status === 403) {
      console.log('Token déjà invalide');
    }
  } finally {
    cleanupLocalTokens();
    redirectToLogin();
  }
}
```

### 3. Déconnexion Automatique (Token Révoqué Détecté)

Si le backend répond 403 sur une requête normale:

```typescript
// Intercepteur global
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 403 &&
        error.response?.data?.detail === 'Could not validate credentials') {

      // Afficher un message à l'utilisateur
      showNotification('Votre session a expiré. Veuillez vous reconnecter.');

      // Nettoyer et rediriger
      cleanupLocalTokens();
      redirectToLogin();
    }

    return Promise.reject(error);
  }
);
```

## Checklist d'Implémentation Frontend

- [ ] Créer une fonction `logout()` qui appelle l'API
- [ ] Envoyer à la fois l'access token (header) et le refresh token (body)
- [ ] Gérer les erreurs réseau gracieusement
- [ ] **TOUJOURS** nettoyer les tokens locaux, même en cas d'erreur
- [ ] Rediriger vers la page de login après logout
- [ ] Ajouter un intercepteur HTTP pour détecter les tokens révoqués (403)
- [ ] Afficher un message de confirmation à l'utilisateur
- [ ] Optionnel: Ajouter une animation/loader pendant le logout

## Test de l'Intégration

### Test Manuel

1. Se connecter normalement
2. Vérifier que les tokens sont stockés
3. Cliquer sur "Se déconnecter"
4. Vérifier que les tokens sont supprimés
5. Vérifier la redirection vers /login
6. Essayer d'accéder à une page protégée (doit rediriger vers login)

### Test avec DevTools

```javascript
// Dans la console du navigateur

// 1. Se connecter et vérifier les tokens
localStorage.getItem('access_token');
localStorage.getItem('refresh_token');

// 2. Se déconnecter
await logout();

// 3. Vérifier que les tokens sont supprimés
localStorage.getItem('access_token');  // null
localStorage.getItem('refresh_token'); // null
```

## Support et Questions

Pour toute question sur l'intégration, consulter:
- Documentation API: http://localhost:8000/docs
- Code backend: `app/api/v1/endpoints/auth.py`
- Tests: `test_logout.sh`
