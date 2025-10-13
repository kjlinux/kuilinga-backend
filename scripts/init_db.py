"""
Script d'initialisation de la base de données
Crée un superuser par défaut
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.user import User
from app.models.organization import Organization
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.device import Device
from app.core.security import get_password_hash


def init_db(db: Session) -> None:
    """Initialiser la base de données avec des données de base"""
    
    # Créer un superuser par défaut
    user = db.query(User).filter(User.email == "admin@kuilinga.com").first()
    if not user:
        user = User(
            email="admin@kuilinga.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Administrateur KUILINGA",
            is_active=True,
            is_superuser=True,
            phone="+225 0000000000"
        )
        db.add(user)
        db.commit()
        print("✅ Superuser créé: admin@kuilinga.com / admin123")
    else:
        print("ℹ️  Superuser existe déjà")
    
    # Créer une organisation de démonstration
    org = db.query(Organization).filter(Organization.name == "KUILINGA Demo").first()
    if not org:
        org = Organization(
            name="KUILINGA Demo",
            description="Organisation de démonstration",
            plan="premium",
            is_active=True,
            email="demo@kuilinga.com",
            phone="+225 0000000000",
            timezone="Africa/Abidjan"
        )
        db.add(org)
        db.commit()
        print("✅ Organisation de démonstration créée")
    else:
        print("ℹ️  Organisation de démonstration existe déjà")
    
    # Créer quelques employés de test
    existing_employees = db.query(Employee).filter(
        Employee.organization_id == org.id
    ).count()
    
    if existing_employees == 0:
        test_employees = [
            {
                "first_name": "Jean",
                "last_name": "Kouassi",
                "email": "jean.kouassi@kuilinga.com",
                "badge_id": "BADGE001",
                "employee_number": "EMP001",
                "department": "IT",
                "position": "Développeur",
                "phone": "+225 0101010101",
                "organization_id": org.id
            },
            {
                "first_name": "Marie",
                "last_name": "Traoré",
                "email": "marie.traore@kuilinga.com",
                "badge_id": "BADGE002",
                "employee_number": "EMP002",
                "department": "RH",
                "position": "Manager RH",
                "phone": "+225 0202020202",
                "organization_id": org.id
            },
            {
                "first_name": "Kofi",
                "last_name": "Yao",
                "email": "kofi.yao@kuilinga.com",
                "badge_id": "BADGE003",
                "employee_number": "EMP003",
                "department": "Commercial",
                "position": "Commercial",
                "phone": "+225 0303030303",
                "organization_id": org.id
            }
        ]
        
        for emp_data in test_employees:
            employee = Employee(**emp_data)
            db.add(employee)
        
        db.commit()
        print(f"✅ {len(test_employees)} employés de test créés")
    else:
        print("ℹ️  Employés de test existent déjà")


def main() -> None:
    """Fonction principale"""
    print("🔧 Création des tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées")
    
    print("\n🔧 Initialisation des données...")
    db = SessionLocal()
    try:
        init_db(db)
        print("\n✅ Base de données initialisée avec succès!")
        print("\n📋 Informations de connexion:")
        print("   Email: admin@kuilinga.com")
        print("   Password: admin123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
