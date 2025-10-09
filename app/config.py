from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import AnyHttpUrl


class Settings(BaseSettings):
    """Configuration de l'application KUILINGA"""
    
    # Info application
    PROJECT_NAME: str = "KUILINGA Backend"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    
    # Base de données
    DATABASE_URL: str = "postgresql://postgres:@127.0.0.1:5432/kuilinga_db"
    
    # Sécurité JWT
    SECRET_KEY: str = "votre-cle-secrete-super-longue-et-aleatoire-changez-moi"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis (cache)
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    
    # CORS - Origins autorisées
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ] # type: ignore
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = "KUILINGA"
    
    # SMS (Africa's Talking)
    SMS_API_KEY: Optional[str] = None
    SMS_USERNAME: Optional[str] = None
    
    # Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 1000
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instance globale des paramètres
settings = Settings()