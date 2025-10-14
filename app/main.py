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

# Initialiser l'application FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API Backend pour le système de gestion de présence KUILINGA",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
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


# Événement d'arrêt
@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions à effectuer à l'arrêt de l'application
    """
    # Arrêter le client MQTT
    mqtt_client.stop()
    print(f"{settings.PROJECT_NAME} arrêté")