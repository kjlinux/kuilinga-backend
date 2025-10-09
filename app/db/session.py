from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Créer le moteur de base de données
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Vérifier la connexion avant utilisation
    pool_size=10,
    max_overflow=20
)

# Session locale
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()


# Dépendance pour obtenir la session DB
def get_db():
    """
    Générateur de session de base de données.
    À utiliser comme dépendance dans les endpoints FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()