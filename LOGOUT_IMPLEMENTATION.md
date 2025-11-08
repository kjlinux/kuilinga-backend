# Implémentation du Logout avec Invalidation des Tokens JWT

## Vue d'ensemble

Cette implémentation ajoute une fonctionnalité complète de déconnexion (logout) au backend Kuilinga avec invalidation des tokens JWT via une liste noire (blacklist).

## Architecture

### 1. Modèle de Base de Données

**Fichier:** [app/models/blacklisted_token.py](app/models/blacklisted_token.py)

Une nouvelle table `blacklisted_tokens` stocke les tokens révoqués:

```python
class BlacklistedToken(BaseModel):
    token = Column(String, unique=True, index=True, nullable=False)
    blacklisted_on = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # Pour nettoyage automatique
    user_id = Column(String, nullable=True)  # Optionnel, pour audit
```

### 2. Opérations CRUD

**Fichier:** [app/crud/blacklisted_token.py](app/crud/blacklisted_token.py)

Fonctions principales:
- `create()` - Ajoute un token à la blacklist
- `is_blacklisted()` - Vérifie si un token est blacklisté
- `remove_expired()` - Supprime les tokens expirés (nettoyage)
- `get_blacklist_count()` - Retourne le nombre de tokens blacklistés

### 3. Sécurité

**Fichier:** [app/core/security.py](app/core/security.py)

Modifications:

#### a) `decode_token()` - Vérification de la Blacklist
```python
def decode_token(token: str, db: Optional[Session] = None) -> dict:
    # Vérifier si le token est blacklisté
    if db and blacklisted_token.is_blacklisted(db, token):
        raise JWTError("Token has been revoked")

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    return payload
```

#### b) `blacklist_token()` - Nouvelle Fonction
```python
def blacklist_token(db: Session, token: str, user_id: Optional[str] = None) -> bool:
    # Décoder pour obtenir la date d'expiration
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    exp = payload.get("exp")
    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)

    # Ajouter à la blacklist
    blacklisted_token.create(db, token=token, expires_at=expires_at, user_id=user_id)
    return True
```

### 4. Endpoint de Logout

**Fichier:** [app/api/v1/endpoints/auth.py](app/api/v1/endpoints/auth.py:86-135)

```python
@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    current_user: models.User = Depends(get_current_active_user),
    refresh_token_data: schemas.RefreshTokenRequest = None,
):
    """
    Déconnecte l'utilisateur en blacklistant son access token et son refresh token.
    """
    # Blacklist l'access token
    access_blacklisted = security.blacklist_token(db, token, current_user.id)

    # Blacklist le refresh token si fourni
    refresh_blacklisted = False
    if refresh_token_data and refresh_token_data.refresh_token:
        refresh_blacklisted = security.blacklist_token(
            db, refresh_token_data.refresh_token, current_user.id
        )

    return {
        "message": "Déconnexion réussie",
        "access_token_revoked": access_blacklisted,
        "refresh_token_revoked": refresh_blacklisted
    }
```

### 5. Service de Nettoyage Automatique

**Fichier:** [app/services/token_cleanup.py](app/services/token_cleanup.py)

Un service en arrière-plan qui nettoie périodiquement les tokens expirés:

```python
class TokenCleanupService:
    def __init__(self, interval_hours: int = 24):
        self.interval_hours = interval_hours

    async def cleanup_expired_tokens(self):
        """Supprime les tokens expirés de la blacklist"""
        db = SessionLocal()
        deleted_count = blacklisted_token.remove_expired(db)
        db.close()
        return deleted_count
```

Le service est démarré automatiquement au lancement de l'application ([app/main.py](app/main.py:114-115)):

```python
@app.on_event("startup")
async def startup_event():
    token_cleanup_service.start()  # Nettoyage toutes les 24h
```

### 6. Migration de Base de Données

**Fichier:** [alembic/versions/120ae6e6ff1b_add_blacklisted_tokens_table.py](alembic/versions/120ae6e6ff1b_add_blacklisted_tokens_table.py)

Migration appliquée avec:
```bash
alembic upgrade head
```

## Utilisation de l'API

### 1. Connexion (Login)

```bash
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password123
```

Réponse:
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    ...
  }
}
```

### 2. Déconnexion (Logout)

```bash
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh_token": "eyJhbGci..."
}
```

Réponse:
```json
{
  "message": "Déconnexion réussie",
  "access_token_revoked": true,
  "refresh_token_revoked": true
}
```

### 3. Comportement après Logout

Toute tentative d'utilisation d'un token blacklisté retournera:

```
HTTP 403 Forbidden
{
  "detail": "Could not validate credentials"
}
```

## Stratégie de Gestion des Erreurs

L'endpoint de logout est conçu pour **toujours réussir** du point de vue du client:

```python
try:
    # Tenter de blacklister les tokens
    access_blacklisted = security.blacklist_token(db, token, current_user.id)
    ...
except Exception as e:
    # En cas d'erreur serveur, retourner quand même un succès
    return {
        "message": "Déconnexion réussie (locale uniquement)",
        "warning": "Les tokens n'ont pas pu être invalidés côté serveur"
    }
```

**Raison:** Le plus important est que le frontend supprime les tokens localement. Même si le backend échoue à les blacklister, l'utilisateur peut se déconnecter localement.

## Flux Complet de Déconnexion

```
1. Frontend → POST /api/v1/auth/logout (avec access token + refresh token)
2. Backend → Valide l'access token
3. Backend → Blackliste l'access token dans la BDD
4. Backend → Blackliste le refresh token dans la BDD
5. Backend → Retourne succès
6. Frontend → Supprime les tokens du localStorage/sessionStorage
7. Frontend → Redirige vers la page de login

Après logout:
8. Utilisateur → Tente d'accéder à une ressource protégée
9. Backend → Vérifie le token → Trouve dans blacklist → 403 Forbidden
```

## Nettoyage et Maintenance

### Nettoyage Automatique

Le service `TokenCleanupService` s'exécute toutes les 24 heures et supprime automatiquement les tokens expirés de la blacklist.

### Nettoyage Manuel

Pour déclencher un nettoyage manuel immédiat:

```python
from app.services.token_cleanup import token_cleanup_service

# Exécuter le nettoyage
deleted_count = await token_cleanup_service.manual_cleanup()
print(f"{deleted_count} tokens expirés supprimés")
```

### Vérifier le Nombre de Tokens Blacklistés

```python
from app.db.session import SessionLocal
from app.crud.blacklisted_token import blacklisted_token

db = SessionLocal()
count = blacklisted_token.get_blacklist_count(db)
print(f"{count} tokens dans la blacklist")
db.close()
```

## Tests

Des scripts de test ont été créés pour valider la fonctionnalité:

### Test Bash (test_logout.sh)
```bash
bash test_logout.sh
```

### Test Refresh Token (test_refresh_blocked.sh)
```bash
bash test_refresh_blocked.sh
```

## Résultats des Tests

```
=== Test de la fonctionnalité de Logout ===

1. Connexion... ✅
2. Vérification que le token fonctionne... ✅
3. Déconnexion (logout)... ✅
   - access_token_revoked: true
   - refresh_token_revoked: true
4. Tentative d'utilisation du token révoqué...
   - HTTP 403: Could not validate credentials ✅

=== Test terminé avec succès ===
```

## Considérations de Performance

1. **Index sur `token`**: La colonne `token` est indexée pour des recherches rapides
2. **Nettoyage périodique**: Les tokens expirés sont supprimés automatiquement pour éviter la croissance infinie de la table
3. **TTL naturel**: Les tokens ont une durée de vie limitée (30 min pour access, 7 jours pour refresh)

## Améliorations Futures Possibles

1. **Redis Cache**: Utiliser Redis pour la blacklist au lieu de PostgreSQL (plus rapide)
2. **Logout Global**: Invalider tous les tokens d'un utilisateur (logout de tous les appareils)
3. **Endpoint Admin**: Ajouter un endpoint pour voir/gérer la blacklist (admin uniquement)
4. **Statistiques**: Tracker les métriques de logout (nombre par jour, par utilisateur, etc.)

## Fichiers Modifiés/Créés

### Nouveaux Fichiers
- `app/models/blacklisted_token.py` - Modèle de la table blacklist
- `app/crud/blacklisted_token.py` - Opérations CRUD pour la blacklist
- `app/services/token_cleanup.py` - Service de nettoyage automatique
- `alembic/versions/120ae6e6ff1b_add_blacklisted_tokens_table.py` - Migration
- `test_logout.sh` - Script de test bash
- `test_refresh_blocked.sh` - Script de test du refresh token

### Fichiers Modifiés
- `app/api/v1/endpoints/auth.py` - Ajout de l'endpoint `/logout`
- `app/core/security.py` - Ajout de `blacklist_token()` et modification de `decode_token()`
- `app/dependencies.py` - Modification de `get_current_user()` pour vérifier la blacklist
- `app/models/__init__.py` - Import du nouveau modèle
- `app/db/base.py` - Import pour Alembic
- `app/main.py` - Démarrage du service de nettoyage

## Documentation API

La documentation interactive Swagger est disponible sur:
- http://localhost:8000/docs

L'endpoint de logout y est documenté avec tous les détails.
