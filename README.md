# 🚀 KUILINGA Backend API

Backend FastAPI pour le système de gestion de présence KUILINGA.

## 📋 Table des matières

- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Démarrage](#démarrage)
- [Documentation API](#documentation-api)
- [Tests](#tests)
- [Structure du projet](#structure-du-projet)

## ✅ Prérequis

- Python 3.11 ou supérieur
- PostgreSQL 14 ou supérieur
- pip (gestionnaire de paquets Python)

## 📦 Installation

### 1. Cloner le projet

```bash
git clone <url-du-repo>
cd kuilinga-backend
```

### 2. Créer l'environnement virtuel

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Créer la base de données PostgreSQL

```bash
# Se connecter à PostgreSQL
psql -U postgres

# Créer la base de données et l'utilisateur
CREATE DATABASE kuilinga_db;
CREATE USER kuilinga_user WITH PASSWORD 'password123';
GRANT ALL PRIVILEGES ON DATABASE kuilinga_db TO kuilinga_user;
\q
```

## ⚙️ Configuration

### 1. Créer le fichier .env

Copiez `.env.example` vers `.env` et modifiez les valeurs:

```env
# Application
PROJECT_NAME="KUILINGA Backend"
VERSION="1.0.0"
API_V1_PREFIX="/api/v1"
DEBUG=True

# Base de données
DATABASE_URL=postgresql://kuilinga_user:password123@localhost:5432/kuilinga_db

# Sécurité JWT
SECRET_KEY=votre-cle-secrete-super-longue-et-aleatoire-changez-moi
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

**⚠️ IMPORTANT**: Changez la `SECRET_KEY` en production!

### 2. Initialiser la base de données

```bash
python scripts/init_db.py
```

Cette commande va:
- Créer toutes les tables
- Créer un compte admin par défaut
- Créer une organisation de démonstration
- Créer quelques employés de test

**Credentials par défaut:**
- Email: `admin@kuilinga.com`
- Password: `admin123`

## 🚀 Démarrage

### Mode développement

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible sur: `http://localhost:8000`

### Mode production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 Documentation API

Une fois l'application lancée, accédez à:

- **Swagger UI (interactive)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## 🔐 Authentification

L'API utilise JWT (JSON Web Tokens) pour l'authentification.

### 1. Obtenir un token

```bash
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@kuilinga.com&password=admin123
```

Réponse:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Utiliser le token

Ajoutez le header à vos requêtes:
```
Authorization: Bearer <access_token>
```

### 3. Rafraîchir le token

```bash
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "votre_refresh_token"
}
```

## 📡 Endpoints principaux

### Authentification
- `POST /api/v1/auth/register` - Créer un compte
- `POST /api/v1/auth/login` - Se connecter
- `POST /api/v1/auth/refresh` - Rafraîchir le token

### Utilisateurs
- `GET /api/v1/users/me` - Profil actuel
- `PUT /api/v1/users/me` - Modifier son profil
- `GET /api/v1/users/` - Liste des utilisateurs (admin)
- `POST /api/v1/users/` - Créer un utilisateur (admin)

### Employés
- `GET /api/v1/employees/` - Liste des employés
- `POST /api/v1/employees/` - Créer un employé
- `GET /api/v1/employees/{id}` - Détails d'un employé
- `PUT /api/v1/employees/{id}` - Modifier un employé
- `DELETE /api/v1/employees/{id}` - Supprimer un employé

### Pointages
- `POST /api/v1/attendance/` - Créer un pointage
- `GET /api/v1/attendance/` - Liste des pointages
- `GET /api/v1/attendance/today` - Pointages du jour
- `GET /api/v1/attendance/stats/daily` - Statistiques quotidiennes
- `GET /api/v1/attendance/employee/{id}` - Historique d'un employé

## 🧪 Tests

```bash
# Lancer tous les tests
pytest

# Avec couverture de code
pytest --cov=app --cov-report=html

# Tests spécifiques
pytest tests/test_api/test_auth.py
```

## 🗂️ Structure du projet

```
kuilinga-backend/
├── app/
│   ├── main.py              # Application FastAPI
│   ├── config.py            # Configuration
│   ├── dependencies.py      # Dépendances
│   ├── api/v1/              # Routes API
│   ├── core/                # Sécurité, permissions
│   ├── models/              # Modèles SQLAlchemy
│   ├── schemas/             # Schémas Pydantic
│   ├── crud/                # Opérations CRUD
│   ├── db/                  # Connexion DB
│   └── services/            # Logique métier
├── tests/                   # Tests
├── scripts/                 # Scripts utilitaires
├── requirements.txt         # Dépendances
└── README.md               # Documentation
```

## 🔧 Migrations de base de données (Alembic)

### Créer une migration

```bash
alembic revision --autogenerate -m "Description de la migration"
```

### Appliquer les migrations

```bash
alembic upgrade head
```

### Revenir en arrière

```bash
alembic downgrade -1
```

## 🐳 Docker (optionnel)

### Lancer avec Docker Compose

```bash
docker-compose up -d
```

### Arrêter

```bash
docker-compose down
```

## 📝 Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `PROJECT_NAME` | Nom du projet | "KUILINGA Backend" |
| `VERSION` | Version de l'API | "1.0.0" |
| `DEBUG` | Mode debug | True |
| `DATABASE_URL` | URL de la base de données | - |
| `SECRET_KEY` | Clé secrète JWT | - |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée de vie access token | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Durée de vie refresh token | 7 |

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT.

## 👥 Auteurs

**TANGA GROUP**

## 📞 Support

Pour toute question ou problème:
- Email: support@kuilinga.com
- Documentation: http://localhost:8000/docs