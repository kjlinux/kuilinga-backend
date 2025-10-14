"""
Script pour nettoyer complètement la base de données
⚠️ ATTENTION: Ce script supprime TOUTES les données!
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.attendance import Attendance
from app.models.leave import Leave
from app.models.device import Device
from app.models.employee import Employee
from app.models.department import Department
from app.models.site import Site
from app.models.role import Role, Permission
from app.models.user import User
from app.models.organization import Organization


def confirm_cleanup():
    """Demander confirmation avant de nettoyer"""
    print("⚠️  ATTENTION: Cette opération va supprimer TOUTES les données!")
    print("⚠️  Cette action est IRRÉVERSIBLE!")
    response = input("\nTaper 'SUPPRIMER' pour confirmer: ")
    return response == "SUPPRIMER"


def cleanup_database(db: Session):
    """Nettoyer toutes les données"""
    print("\n🗑️  Suppression des données...")
    
    try:
        # Supprimer dans l'ordre inverse des dépendances
        print("  • Suppression des congés...")
        db.query(Leave).delete()
        
        print("  • Suppression des pointages...")
        db.query(Attendance).delete()
        
        print("  • Suppression des employés...")
        db.query(Employee).delete()
        
        print("  • Suppression des départements...")
        db.query(Department).delete()
        
        print("  • Suppression des dispositifs...")
        db.query(Device).delete()
        
        print("  • Suppression des utilisateurs...")
        db.query(User).delete()
        
        print("  • Suppression des rôles et permissions...")
        db.query(Role).delete()
        db.query(Permission).delete()
        
        print("  • Suppression des sites...")
        db.query(Site).delete()
        
        print("  • Suppression des organisations...")
        db.query(Organization).delete()
        
        db.commit()
        print("\n✅ Base de données nettoyée avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du nettoyage: {str(e)}")
        db.rollback()
        raise


def drop_all_tables():
    """Supprimer toutes les tables (option nucléaire)"""
    print("\n💣 Suppression de TOUTES les tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Toutes les tables ont été supprimées!")
    
    print("\n🔨 Recréation des tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables recréées!")


def main():
    """Fonction principale"""
    print("=" * 60)
    print("🗑️  NETTOYAGE DE LA BASE DE DONNÉES KUILINGA")
    print("=" * 60)
    
    print("\nOptions:")
    print("  1. Nettoyer les données (garder les tables)")
    print("  2. Supprimer et recréer toutes les tables")
    print("  3. Annuler")
    
    choice = input("\nVotre choix (1/2/3): ")
    
    if choice == "1":
        if confirm_cleanup():
            db = SessionLocal()
            try:
                cleanup_database(db)
            finally:
                db.close()
        else:
            print("\n❌ Opération annulée")
    
    elif choice == "2":
        if confirm_cleanup():
            drop_all_tables()
        else:
            print("\n❌ Opération annulée")
    
    else:
        print("\n❌ Opération annulée")


if __name__ == "__main__":
    main()