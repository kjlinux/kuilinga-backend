"""
Script rapide pour peupler la base de données avec des données minimales de test
Parfait pour le développement rapide
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, date, time

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
from app.models.device import DeviceStatus
from app.core.security import get_password_hash


def quick_seed(db: Session):
    """Seed rapide avec données minimales"""
    
    print("🚀 Seed rapide de la base de données...")
    
    # 1. Permissions essentielles
    perms = {}
    essential_perms = [
        {"name": "attendance:create", "description": "Créer un pointage"},
        {"name": "attendance:read", "description": "Lire les pointages"},
        {"name": "leave:create", "description": "Créer un congé"},
        {"name": "leave:read", "description": "Lire les congés"},
        {"name": "leave:approve", "description": "Approuver un congé"},
    ]
    
    for perm_data in essential_perms:
        perm = Permission(**perm_data)
        db.add(perm)
        db.flush()
        perms[perm.name] = perm
    print("  ✓ Permissions créées")
    
    # 2. Rôles de base
    role_admin = Role(name="Admin", description="Administrateur")
    role_admin.permissions.extend(perms.values())
    db.add(role_admin)
    
    role_employee = Role(name="Employé", description="Employé standard")
    role_employee.permissions.extend([perms["attendance:create"], perms["attendance:read"], perms["leave:create"], perms["leave:read"]])
    db.add(role_employee)
    db.flush()
    print("  ✓ Rôles créés")
    
    # 3. Organisation
    org = Organization(
        name="Test Company",
        email="contact@test.com",
        phone="+225 01 02 03 04 05",
        timezone="Africa/Abidjan",
        plan="premium",
        is_active=True,
    )
    db.add(org)
    db.flush()
    print("  ✓ Organisation créée")
    
    # 4. Site
    site = Site(
        name="Siège Principal",
        address="Abidjan, Plateau",
        timezone="Africa/Abidjan",
        organization_id=org.id,
    )
    db.add(site)
    db.flush()
    print("  ✓ Site créé")
    
    # 5. Département
    dept = Department(
        name="Informatique",
        site_id=site.id,
    )
    db.add(dept)
    db.flush()
    print("  ✓ Département créé")
    
    # 6. Super Admin
    admin = User(
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Admin Test",
        is_active=True,
        is_superuser=True,
        phone="+225 07 00 00 00 01",
        organization_id=org.id,
    )
    admin.roles.append(role_admin)
    db.add(admin)
    db.flush()
    print("  ✓ Admin créé: admin@test.com / admin123")
    
    # 7. Employés de test
    employees_data = [
        {"first": "Kouassi", "last": "Jean", "position": "Développeur"},
        {"first": "Yao", "last": "Marie", "position": "Manager IT"},
        {"first": "Traoré", "last": "Ibrahim", "position": "Support"},
    ]
    
    employees = []
    for i, emp_data in enumerate(employees_data, 1):
        email = f"{emp_data['first'].lower()}.{emp_data['last'].lower()}@test.com"
        
        user = User(
            email=email,
            hashed_password=get_password_hash("password123"),
            full_name=f"{emp_data['first']} {emp_data['last']}",
            is_active=True,
            is_superuser=False,
            phone=f"+225 07 00 00 00 {10+i:02d}",
            organization_id=org.id,
        )
        user.roles.append(role_admin if i == 2 else role_employee)
        db.add(user)
        db.flush()
        
        employee = Employee(
            first_name=emp_data['first'],
            last_name=emp_data['last'],
            email=email,
            phone=user.phone,
            employee_number=f"EMP{i:03d}",
            badge_id=f"BADGE{i:03d}",
            position=emp_data['position'],
            user_id=user.id,
            organization_id=org.id,
            site_id=site.id,
            department_id=dept.id,
        )
        db.add(employee)
        db.flush()
        employees.append(employee)
        
        # Le manager du département
        if i == 2:
            dept.manager_id = employee.id
    
    print(f"  ✓ {len(employees)} employés créés")
    
    # 8. Dispositif
    device = Device(
        serial_number="DEV-001",
        type="Terminal Biométrique",
        status=DeviceStatus.ONLINE,
        organization_id=org.id,
        site_id=site.id,
    )
    db.add(device)
    db.flush()
    print("  ✓ Dispositif créé")
    
    # 9. Pointages des 7 derniers jours
    today = datetime.now().date()
    attendance_count = 0
    
    for employee in employees:
        for day_offset in range(7):
            current_date = today - timedelta(days=day_offset)
            
            # Sauter le weekend
            if current_date.weekday() >= 5:
                continue
            
            # Entrée
            att_in = Attendance(
                timestamp=datetime.combine(current_date, time(8, 30)),
                type=AttendanceType.IN,
                employee_id=employee.id,
                device_id=device.id,
            )
            db.add(att_in)
            
            # Sortie
            att_out = Attendance(
                timestamp=datetime.combine(current_date, time(17, 30)),
                type=AttendanceType.OUT,
                employee_id=employee.id,
                device_id=device.id,
            )
            db.add(att_out)
            attendance_count += 2
    
    print(f"  ✓ {attendance_count} pointages créés")
    
    # 10. Demandes de congés
    leave1 = Leave(
        employee_id=employees[0].id,
        leave_type=LeaveType.ANNUAL,
        start_date=today + timedelta(days=10),
        end_date=today + timedelta(days=15),
        reason="Vacances annuelles",
        status=LeaveStatus.PENDING,
    )
    db.add(leave1)
    
    leave2 = Leave(
        employee_id=employees[1].id,
        leave_type=LeaveType.SICK,
        start_date=today - timedelta(days=2),
        end_date=today - timedelta(days=1),
        reason="Maladie",
        status=LeaveStatus.APPROVED,
        approver_id=admin.id,
    )
    db.add(leave2)
    
    print("  ✓ 2 demandes de congés créées")
    
    db.commit()
    
    print("\n✅ Seed rapide terminé!")
    print("\n📋 Comptes créés:")
    print("  • admin@test.com / admin123 (Super Admin)")
    print("  • kouassi.jean@test.com / password123 (Employé)")
    print("  • yao.marie@test.com / password123 (Manager)")
    print("  • traore.ibrahim@test.com / password123 (Support)")


def main():
    """Fonction principale"""
    db = SessionLocal()
    try:
        quick_seed(db)
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()