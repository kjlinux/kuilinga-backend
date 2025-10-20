"""
Script complet pour peupler la base de données avec des données réalistes
Crée: Organizations, Sites, Departments, Users, Roles, Permissions, Employees, Devices, Attendances, Leaves
Inclut toutes les permissions de seed.py et seed_data.py
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, date, time
import random

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.site import Site
from app.models.department import Department
from app.models.employee import Employee
from app.models.device import Device
from app.models.attendance import Attendance, AttendanceType
from app.models.leave import Leave, LeaveStatus, LeaveType
from app.models.role import Role, Permission
from app.core.security import get_password_hash


# ==================== PERMISSIONS (FUSIONNÉES) ====================
PERMISSIONS_DATA = [
    # User management
    {"name": "user:create", "description": "Créer un utilisateur"},
    {"name": "user:read", "description": "Lire les utilisateurs"},
    {"name": "user:update", "description": "Mettre à jour un utilisateur"},
    {"name": "user:delete", "description": "Supprimer un utilisateur"},
    
    # Employee management
    {"name": "employee:create", "description": "Créer un employé"},
    {"name": "employee:read", "description": "Lire les employés"},
    {"name": "employee:update", "description": "Mettre à jour un employé"},
    {"name": "employee:delete", "description": "Supprimer un employé"},
    
    # Department management
    {"name": "department:create", "description": "Créer un département"},
    {"name": "department:read", "description": "Lire les départements"},
    {"name": "department:update", "description": "Mettre à jour un département"},
    {"name": "department:delete", "description": "Supprimer un département"},
    
    # Attendance management
    {"name": "attendance:create", "description": "Créer un pointage"},
    {"name": "attendance:read", "description": "Lire les pointages"},
    {"name": "attendance:read:all", "description": "Lire tous les pointages"},
    {"name": "attendance:update", "description": "Mettre à jour un pointage"},
    {"name": "attendance:delete", "description": "Supprimer un pointage"},
    
    # Leave management
    {"name": "leave:create", "description": "Créer une demande de congé"},
    {"name": "leave:read", "description": "Lire les congés"},
    {"name": "leave:read:all", "description": "Lire tous les congés"},
    {"name": "leave:approve", "description": "Approuver un congé"},
    {"name": "leave:reject", "description": "Rejeter un congé"},
    
    # Role management
    {"name": "role:create", "description": "Créer un rôle"},
    {"name": "role:read", "description": "Lire les rôles"},
    {"name": "role:update", "description": "Mettre à jour un rôle"},
    {"name": "role:delete", "description": "Supprimer un rôle"},
    {"name": "role:assign", "description": "Assigner un rôle"},
    {"name": "role:assign_permission", "description": "Assigner une permission à un rôle"},
    
    # Permission management
    {"name": "permission:read", "description": "Lire les permissions"},
    
    # Device management
    {"name": "device:create", "description": "Créer un appareil"},
    {"name": "device:read", "description": "Lire les appareils"},
    {"name": "device:update", "description": "Mettre à jour un appareil"},
    {"name": "device:delete", "description": "Supprimer un appareil"},
    
    # Reports - From seed.py (R1-R20)
    {"name": "report:generate", "description": "Générer des rapports"},
    {"name": "report:export", "description": "Exporter des rapports"},
    {"name": "report:R1:view", "description": "Voir le rapport consolidé multi-organisations"},
    {"name": "report:R2:view", "description": "Voir l'analyse comparative inter-organisations"},
    {"name": "report:R3:view", "description": "Voir le rapport d'utilisation des devices"},
    {"name": "report:R4:view", "description": "Voir l'audit des utilisateurs et rôles"},
    {"name": "report:R5:view", "description": "Voir le rapport de présence globale organisation"},
    {"name": "report:R6:view", "description": "Voir le rapport mensuel synthétique"},
    {"name": "report:R7:view", "description": "Voir l'analyse des absences et congés"},
    {"name": "report:R8:view", "description": "Voir le rapport des retards et anomalies"},
    {"name": "report:R9:view", "description": "Voir le rapport heures travaillées par employé"},
    {"name": "report:R10:view", "description": "Voir le rapport d'activité par site"},
    {"name": "report:R11:view", "description": "Voir l'export paie"},
    {"name": "report:R12:view", "description": "Voir le rapport de présence département"},
    {"name": "report:R13:view", "description": "Voir le rapport hebdomadaire équipe"},
    {"name": "report:R14:view", "description": "Voir la validation des heures"},
    {"name": "report:R15:view", "description": "Voir les demandes de congés"},
    {"name": "report:R16:view", "description": "Voir la performance présence équipe"},
    {"name": "report:R17:view", "description": "Voir son relevé de présence"},
    {"name": "report:R18:view", "description": "Voir son récapitulatif mensuel"},
    {"name": "report:R19:view", "description": "Voir ses congés"},
    {"name": "report:R20:view", "description": "Voir son attestation de présence"},
]

# ==================== ROLES (FUSIONNÉS) ====================
ROLES_DATA = {
    "Super Administrateur": {
        "description": "Accès complet à toutes les fonctionnalités du système",
        "permissions": [p["name"] for p in PERMISSIONS_DATA],
    },
    "Administrateur système": {
        "description": "Accès complet à toutes les fonctionnalités du système (alias)",
        "permissions": [p["name"] for p in PERMISSIONS_DATA],
    },
    "Administrateur RH": {
        "description": "Gère les employés, congés et rapports RH",
        "permissions": [
            "user:read", "user:update",
            "employee:create", "employee:read", "employee:update", "employee:delete",
            "department:read", "department:update",
            "attendance:read:all", "attendance:create",
            "leave:read:all", "leave:approve", "leave:reject",
            "report:generate", "report:export",
            "report:R5:view", "report:R6:view", "report:R7:view", 
            "report:R8:view", "report:R9:view", "report:R10:view", "report:R11:view",
        ],
    },
    "Manager / Responsable RH": {
        "description": "Gère les équipes, valide les absences et consulte les rapports",
        "permissions": [
            "department:read",
            "employee:read",
            "attendance:read:all", "attendance:create",
            "leave:read:all", "leave:approve", "leave:reject",
            "report:generate",
            "report:R5:view", "report:R6:view", "report:R7:view",
            "report:R8:view", "report:R9:view", "report:R10:view", "report:R11:view",
        ],
    },
    "Manager": {
        "description": "Gère son équipe et valide les congés",
        "permissions": [
            "employee:read",
            "department:read",
            "attendance:read:all",
            "leave:read:all", "leave:approve", "leave:reject",
            "report:generate",
        ],
    },
    "Manager de département": {
        "description": "Gère une équipe spécifique et accède aux rapports départementaux",
        "permissions": [
            "department:read",
            "employee:read",
            "attendance:read:all",
            "leave:read:all", "leave:approve", "leave:reject",
            "report:R12:view", "report:R13:view", "report:R14:view",
            "report:R15:view", "report:R16:view",
        ],
    },
    "Employé": {
        "description": "Peut pointer et gérer ses propres congés",
        "permissions": [
            "attendance:create", "attendance:read",
            "leave:create", "leave:read",
            "report:R17:view", "report:R18:view", "report:R19:view", "report:R20:view",
        ],
    },
    "Employé / Étudiant": {
        "description": "Peut pointer et consulter son historique personnel (alias)",
        "permissions": [
            "attendance:create", "attendance:read",
            "leave:create", "leave:read",
            "report:R17:view", "report:R18:view", "report:R19:view", "report:R20:view",
        ],
    },
    "Superviseur": {
        "description": "Supervise les pointages et peut générer des rapports",
        "permissions": [
            "employee:read",
            "attendance:read:all",
            "leave:read:all",
            "report:generate",
            "report:R5:view", "report:R10:view", "report:R12:view",
        ],
    },
}


def create_permissions(db: Session) -> dict:
    """Créer toutes les permissions (fusionnées des deux scripts)"""
    print("\n📋 Création des permissions...")
    permissions = {}
    
    for perm_data in PERMISSIONS_DATA:
        perm = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
        if not perm:
            perm = Permission(**perm_data)
            db.add(perm)
            db.flush()
            print(f"  ✓ Permission créée: {perm.name}")
        else:
            print(f"  ℹ Permission existante: {perm.name}")
        permissions[perm.name] = perm
    
    db.commit()
    print(f"✅ {len(permissions)} permissions traitées")
    return permissions


def create_roles(db: Session, permissions: dict) -> dict:
    """Créer tous les rôles avec leurs permissions (fusionnés des deux scripts)"""
    print("\n👥 Création des rôles...")
    roles = {}
    
    for role_name, role_data in ROLES_DATA.items():
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(name=role_name, description=role_data["description"])
            db.add(role)
            db.flush()
            
            # Assigner les permissions
            role_permissions = [permissions[pname] for pname in role_data["permissions"] if pname in permissions]
            role.permissions.extend(role_permissions)
            
            print(f"  ✓ Rôle créé: {role_name} ({len(role_permissions)} permissions)")
        else:
            # Mettre à jour les permissions du rôle existant
            existing_perm_names = {p.name for p in role.permissions}
            new_permissions = [
                permissions[pname] 
                for pname in role_data["permissions"] 
                if pname in permissions and pname not in existing_perm_names
            ]
            if new_permissions:
                role.permissions.extend(new_permissions)
                print(f"  ↻ Rôle mis à jour: {role_name} (+{len(new_permissions)} permissions)")
            else:
                print(f"  ℹ Rôle existant: {role_name}")
        
        roles[role_name] = role
    
    db.commit()
    print(f"✅ {len(roles)} rôles traités")
    return roles


def create_organizations(db: Session) -> list:
    """Créer des organisations"""
    print("\n🏢 Création des organisations...")
    organizations_data = [
        {
            "name": "KUILINGA Tech",
            "description": "Entreprise technologique innovante basée à Abidjan",
            "email": "contact@kuilinga.tech",
            "phone": "+225 27 20 12 34 56",
            "timezone": "Africa/Abidjan",
            "plan": "enterprise",
            "is_active": True,
        },
        {
            "name": "Université Félix Houphouët-Boigny",
            "description": "Principale université publique de Côte d'Ivoire",
            "email": "admin@univ-fhb.edu.ci",
            "phone": "+225 27 22 44 10 88",
            "timezone": "Africa/Abidjan",
            "plan": "premium",
            "is_active": True,
        },
    ]
    
    organizations = []
    for org_data in organizations_data:
        org = db.query(Organization).filter(Organization.name == org_data["name"]).first()
        if not org:
            org = Organization(**org_data)
            db.add(org)
            db.flush()
            print(f"  ✓ Organisation créée: {org.name}")
        else:
            print(f"  ℹ Organisation existante: {org.name}")
        organizations.append(org)
    
    db.commit()
    print(f"✅ {len(organizations)} organisations traitées")
    return organizations


def create_sites(db: Session, organizations: list) -> list:
    """Créer des sites pour chaque organisation"""
    print("\n📍 Création des sites...")
    sites_data = {
        "KUILINGA Tech": [
            {"name": "Siège Social - Plateau", "address": "Avenue Chardy, Plateau, Abidjan", "timezone": "Africa/Abidjan"},
            {"name": "Centre R&D - Cocody", "address": "Riviera 2, Cocody, Abidjan", "timezone": "Africa/Abidjan"},
            {"name": "Agence Bouaké", "address": "Commerce, Bouaké", "timezone": "Africa/Abidjan"},
        ],
        "Université Félix Houphouët-Boigny": [
            {"name": "Campus Principal - Cocody", "address": "BP V 34 Abidjan, Cocody", "timezone": "Africa/Abidjan"},
            {"name": "Annexe Abobo", "address": "Abobo, Abidjan", "timezone": "Africa/Abidjan"},
        ],
    }
    
    sites = []
    for org in organizations:
        if org.name in sites_data:
            for site_data in sites_data[org.name]:
                site = db.query(Site).filter(
                    Site.name == site_data["name"],
                    Site.organization_id == org.id
                ).first()
                if not site:
                    site = Site(**site_data, organization_id=org.id)
                    db.add(site)
                    db.flush()
                    print(f"  ✓ Site créé: {site.name}")
                else:
                    print(f"  ℹ Site existant: {site.name}")
                sites.append(site)
    
    db.commit()
    print(f"✅ {len(sites)} sites traités")
    return sites


def create_departments(db: Session, sites: list) -> list:
    """Créer des départements pour chaque site"""
    print("\n🏛️ Création des départements...")
    departments_data = {
        "Siège Social - Plateau": ["Direction Générale", "Ressources Humaines", "Finance", "IT", "Marketing"],
        "Centre R&D - Cocody": ["Recherche", "Développement", "Innovation", "Qualité"],
        "Agence Bouaké": ["Commercial", "Support Client"],
        "Campus Principal - Cocody": ["Administration", "Informatique", "Sécurité", "Maintenance"],
        "Annexe Abobo": ["Administration", "Enseignement"],
    }
    
    departments = []
    for site in sites:
        if site.name in departments_data:
            for dept_name in departments_data[site.name]:
                dept = db.query(Department).filter(
                    Department.name == dept_name,
                    Department.site_id == site.id
                ).first()
                if not dept:
                    dept = Department(name=dept_name, site_id=site.id)
                    db.add(dept)
                    db.flush()
                    print(f"  ✓ Département créé: {dept_name} @ {site.name}")
                else:
                    print(f"  ℹ Département existant: {dept_name} @ {site.name}")
                departments.append(dept)
    
    db.commit()
    print(f"✅ {len(departments)} départements traités")
    return departments


def create_users_and_employees(db: Session, organizations: list, sites: list, departments: list, roles: dict) -> tuple:
    """Créer des utilisateurs et employés réalistes"""
    print("\n👤 Création des utilisateurs et employés...")
    
    # Données réalistes pour la Côte d'Ivoire
    first_names = ["Kouassi", "Yao", "Koné", "Ouattara", "Traoré", "Bamba", "N'Guessan", "Diallo", 
                   "Coulibaly", "Touré", "Aya", "Adjoua", "Akissi", "Amenan", "Affoue"]
    last_names = ["Jean", "Marie", "Ibrahim", "Fatou", "Abdoul", "Aïcha", "Mohamed", "Mariama",
                  "Moussa", "Aminata", "Seydou", "Fatoumata", "Awa", "Karim", "Rokia"]
    positions_by_dept = {
        "Direction Générale": ["Directeur Général", "Directeur Adjoint", "Assistant de Direction"],
        "Ressources Humaines": ["DRH", "Chargé de Recrutement", "Gestionnaire RH", "Assistant RH"],
        "Finance": ["Directeur Financier", "Comptable", "Contrôleur de Gestion", "Assistant Comptable"],
        "IT": ["CTO", "Développeur Senior", "Développeur", "DevOps Engineer", "Support Technique"],
        "Marketing": ["Directeur Marketing", "Chef de Produit", "Community Manager", "Designer"],
        "Recherche": ["Chef de Projet R&D", "Chercheur", "Ingénieur R&D"],
        "Développement": ["Lead Developer", "Développeur Full-Stack", "Développeur Frontend", "Développeur Backend"],
        "Commercial": ["Directeur Commercial", "Commercial Senior", "Commercial", "Assistant Commercial"],
        "Administration": ["Administrateur", "Secrétaire", "Agent Administratif"],
        "Sécurité": ["Chef de Sécurité", "Agent de Sécurité"],
    }
    
    users = []
    employees = []
    employee_counter = 1
    
    # Créer le super admin
    admin = db.query(User).filter(User.email == "admin@kuilinga.com").first()
    if not admin:
        admin = User(
            email="admin@kuilinga.com",
            hashed_password=get_password_hash("Admin@123"),
            full_name="Administrateur Système",
            is_active=True,
            is_superuser=True,
            phone="+225 07 00 00 00 00",
            organization_id=organizations[0].id
        )
        db.add(admin)
        admin.roles.append(roles.get("Super Administrateur") or roles.get("Administrateur système"))
        db.flush()
        print(f"  ✓ Super Admin créé: admin@kuilinga.com")
        users.append(admin)
    else:
        print(f"  ℹ Super Admin existant: admin@kuilinga.com")
        users.append(admin)
    
    # Créer des utilisateurs/employés pour chaque département
    for dept in departments:
        site = next(s for s in sites if s.id == dept.site_id)
        org = next(o for o in organizations if o.id == site.organization_id)
        
        dept_positions = positions_by_dept.get(dept.name, ["Employé", "Assistant", "Manager"])
        num_employees = min(len(dept_positions), random.randint(3, 6))
        
        for i in range(num_employees):
            first = random.choice(first_names)
            last = random.choice(last_names)
            email = f"{first.lower()}.{last.lower()}{employee_counter}@{org.name.lower().replace(' ', '')}.com"
            
            # Créer l'utilisateur
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    email=email,
                    hashed_password=get_password_hash("Password@123"),
                    full_name=f"{first} {last}",
                    is_active=True,
                    is_superuser=False,
                    phone=f"+225 07 {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}",
                    organization_id=org.id
                )
                db.add(user)
                db.flush()
                
                # Assigner un rôle
                if i == 0:  # Premier employé = Manager
                    user.roles.append(roles.get("Manager") or roles.get("Manager de département"))
                elif "RH" in dept.name or "Ressources Humaines" in dept.name:
                    user.roles.append(roles.get("Administrateur RH") or roles.get("Manager / Responsable RH"))
                else:
                    user.roles.append(roles.get("Employé") or roles.get("Employé / Étudiant"))
                
                users.append(user)
            
            # Créer l'employé
            employee = db.query(Employee).filter(Employee.email == email).first()
            if not employee:
                employee = Employee(
                    first_name=first,
                    last_name=last,
                    email=email,
                    phone=user.phone,
                    employee_number=f"EMP{employee_counter:04d}",
                    badge_id=f"BADGE{employee_counter:04d}",
                    position=dept_positions[i % len(dept_positions)],
                    user_id=user.id,
                    organization_id=org.id,
                    site_id=site.id,
                    department_id=dept.id,
                )
                db.add(employee)
                db.flush()
                employees.append(employee)
                
                # Assigner le premier employé comme manager du département
                if i == 0 and not dept.manager_id:
                    dept.manager_id = employee.id
                
                employee_counter += 1
    
    db.commit()
    print(f"✅ {len(users)} utilisateurs traités")
    print(f"✅ {len(employees)} employés traités")
    return users, employees


def create_devices(db: Session, organizations: list, sites: list) -> list:
    """Créer des dispositifs de pointage"""
    print("\n📱 Création des dispositifs...")
    from app.models.device import DeviceStatus
    
    devices = []
    device_counter = 1
    
    for site in sites:
        org = next(o for o in organizations if o.id == site.organization_id)
        num_devices = random.randint(2, 5)
        
        for i in range(num_devices):
            serial = f"KLG-{device_counter:06d}"
            device = db.query(Device).filter(Device.serial_number == serial).first()
            if not device:
                device = Device(
                    serial_number=serial,
                    type=random.choice(["Terminal Fixe", "Lecteur Biométrique", "Lecteur RFID", "Mobile App"]),
                    status=random.choice([DeviceStatus.ONLINE, DeviceStatus.ONLINE, DeviceStatus.OFFLINE]),
                    organization_id=org.id,
                    site_id=site.id,
                )
                db.add(device)
                db.flush()
                devices.append(device)
                device_counter += 1
    
    db.commit()
    print(f"✅ {len(devices)} dispositifs traités")
    return devices


def create_attendances(db: Session, employees: list, devices: list) -> list:
    """Créer des pointages réalistes pour les 30 derniers jours"""
    print("\n⏰ Création des pointages...")
    
    attendances = []
    today = datetime.now().date()
    
    for employee in employees[:50]:  # Limiter aux 50 premiers pour ne pas surcharger
        # Pointages pour les 30 derniers jours
        for day_offset in range(30):
            current_date = today - timedelta(days=day_offset)
            
            # Sauter les weekends
            if current_date.weekday() >= 5:
                continue
            
            # 90% de chance d'être présent
            if random.random() > 0.9:
                continue
            
            # Heure d'arrivée entre 7h30 et 9h30
            arrival_hour = random.randint(7, 9)
            arrival_minute = random.randint(0, 59)
            arrival_time = datetime.combine(current_date, time(arrival_hour, arrival_minute))
            
            # Heure de départ entre 17h et 19h
            departure_hour = random.randint(17, 19)
            departure_minute = random.randint(0, 59)
            departure_time = datetime.combine(current_date, time(departure_hour, departure_minute))
            
            device = random.choice(devices)
            
            # Pointage d'entrée
            att_in = Attendance(
                timestamp=arrival_time,
                type=AttendanceType.IN,
                geo=f"5.{random.randint(3000,3500)}, -4.{random.randint(1,9999):04d}",
                employee_id=employee.id,
                device_id=device.id,
            )
            db.add(att_in)
            attendances.append(att_in)
            
            # Pointage de sortie
            att_out = Attendance(
                timestamp=departure_time,
                type=AttendanceType.OUT,
                geo=f"5.{random.randint(3000,3500)}, -4.{random.randint(1,9999):04d}",
                employee_id=employee.id,
                device_id=device.id,
            )
            db.add(att_out)
            attendances.append(att_out)
    
    db.commit()
    print(f"✅ {len(attendances)} pointages créés")
    return attendances


def create_leaves(db: Session, employees: list, users: list) -> list:
    """Créer des demandes de congés"""
    print("\n🏖️ Création des congés...")
    
    leaves = []
    today = date.today()
    
    for employee in random.sample(employees, min(20, len(employees))):
        # 1-3 demandes de congés par employé
        num_leaves = random.randint(1, 3)
        
        for _ in range(num_leaves):
            start_offset = random.randint(-60, 60)
            duration = random.randint(2, 15)
            
            start_date = today + timedelta(days=start_offset)
            end_date = start_date + timedelta(days=duration)
            
            leave = Leave(
                employee_id=employee.id,
                leave_type=random.choice(list(LeaveType)),
                start_date=start_date,
                end_date=end_date,
                reason=random.choice([
                    "Congés annuels",
                    "Raisons familiales",
                    "Maladie",
                    "Rendez-vous médical",
                    "Événement personnel",
                ]),
                status=random.choice([LeaveStatus.PENDING, LeaveStatus.APPROVED, LeaveStatus.APPROVED]),
                approver_id=random.choice(users).id if random.random() > 0.3 else None,
            )
            db.add(leave)
            leaves.append(leave)
    
    db.commit()
    print(f"✅ {len(leaves)} demandes de congés créées")
    return leaves


def main():
    """Fonction principale"""
    print("=" * 60)
    print("🚀 SEED COMPLET DE LA BASE DE DONNÉES KUILINGA")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Créer les données dans l'ordre des dépendances
        permissions = create_permissions(db)
        roles = create_roles(db, permissions)
        organizations = create_organizations(db)
        sites = create_sites(db, organizations)
        departments = create_departments(db, sites)
        users, employees = create_users_and_employees(db, organizations, sites, departments, roles)
        devices = create_devices(db, organizations, sites)
        attendances = create_attendances(db, employees, devices)
        leaves = create_leaves(db, employees, users)
        
        print("\n" + "=" * 60)
        print("✅ BASE DE DONNÉES PEUPLÉE AVEC SUCCÈS!")
        print("=" * 60)
        print("\n📊 RÉSUMÉ:")
        print(f"  • {len(permissions)} permissions")
        print(f"  • {len(roles)} rôles")
        print(f"  • {len(organizations)} organisations")
        print(f"  • {len(sites)} sites")
        print(f"  • {len(departments)} départements")
        print(f"  • {len(users)} utilisateurs")
        print(f"  • {len(employees)} employés")
        print(f"  • {len(devices)} dispositifs")
        print(f"  • {len(attendances)} pointages")
        print(f"  • {len(leaves)} demandes de congés")
        
        print("\n🔐 COMPTES DE TEST:")
        print("  • Super Admin:")
        print("    Email: admin@kuilinga.com")
        print("    Password: Admin@123")
        print("\n  • Tous les autres utilisateurs:")
        print("    Password: Password@123")
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()