from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import time
from app.config import settings
from app.api.v1.api import api_router
from app.db.session import engine, Base

# Créer les tables (en développement - en production utiliser Alembic)
Base.metadata.create_all(bind=engine)

# Métadonnées des tags pour la documentation OpenAPI
tags_metadata = [
    {"name": "Authentification", "description": "Endpoints pour l'authentification JWT (login, refresh, logout)"},
    {"name": "Utilisateurs", "description": "Gestion des comptes utilisateurs et leurs rôles"},
    {"name": "Organisations", "description": "Gestion des organisations (tenants) du système"},
    {"name": "Employés", "description": "Gestion des employés, leurs profils et affectations"},
    {"name": "Devices IoT", "description": "Gestion des terminaux de pointage connectés"},
    {"name": "Pointages", "description": "Enregistrement et consultation des entrées/sorties"},
    {"name": "Rapports", "description": "Génération de rapports PDF, Excel et CSV"},
    {"name": "Départements", "description": "Gestion des départements au sein des organisations"},
    {"name": "Rôles & Permissions", "description": "Gestion du contrôle d'accès basé sur les rôles (RBAC)"},
    {"name": "WebSockets", "description": "Connexions temps réel pour les mises à jour en direct"},
    {"name": "Sites", "description": "Gestion des sites/localisations des organisations"},
    {"name": "Leaves", "description": "Gestion des congés et absences des employés"},
    {"name": "Dashboard", "description": "Statistiques et métriques pour les tableaux de bord"},
    {"name": "Health", "description": "Vérification de l'état de santé de l'API"},
    {"name": "Root", "description": "Point d'entrée de l'API"},
]

# Initialiser l'application FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API Backend pour le système de gestion de présence KUILINGA",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware pour mesurer le temps de réponse
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Gestionnaire d'erreurs de validation
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "message": "Erreur de validation des données"
        },
    )


# Gestionnaire d'erreurs de base de données
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Erreur de base de données",
            "detail": str(exc) if settings.DEBUG else "Une erreur est survenue"
        },
    )


# Route de santé
@app.get("/health", tags=["Health"])
def health_check():
    """
    Vérifier l'état de santé de l'API
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "project": settings.PROJECT_NAME
    }


# Route racine
@app.get("/", tags=["Root"])
def root():
    """
    Route racine - Informations sur l'API
    """
    return {
        "message": f"Bienvenue sur {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }


# Inclure les routes API v1
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


from app.services.mqtt_client import mqtt_client
from app.services.token_cleanup import token_cleanup_service
from app.services.device_status_monitor import device_status_monitor

# Événement de démarrage
@app.on_event("startup")
async def startup_event():
    """
    Actions à effectuer au démarrage de l'application
    """
    print(f"{settings.PROJECT_NAME} v{settings.VERSION} démarré")
    print(f"Documentation disponible sur: /docs")
    print(f"Mode Debug: {settings.DEBUG}")
    # Démarrer le client MQTT
    mqtt_client.start()
    # Démarrer le service de nettoyage des tokens expirés
    token_cleanup_service.start()
    # Démarrer le service de surveillance des devices (heartbeat)
    device_status_monitor.start()


# Événement d'arrêt
@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions à effectuer à l'arrêt de l'application
    """
    # Arrêter le client MQTT
    mqtt_client.stop()
    # Arrêter le service de nettoyage des tokens
    await token_cleanup_service.stop()
    # Arrêter le service de surveillance des devices
    await device_status_monitor.stop()
    print(f"{settings.PROJECT_NAME} arrêté")