import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.crud import role as crud_role
from app.crud import permission as crud_permission
from app.schemas.role import RoleCreate, PermissionCreate

# Définition de toutes les permissions de l'application
PERMISSIONS = [
    # Permissions pour les départements
    {"name": "department:create", "description": "Créer un département"},
    {"name": "department:read", "description": "Lire les départements"},
    {"name": "department:update", "description": "Mettre à jour un département"},
    {"name": "department:delete", "description": "Supprimer un département"},
    # Permissions pour les rôles
    {"name": "role:create", "description": "Créer un rôle"},
    {"name": "role:read", "description": "Lire les rôles"},
    {"name": "role:update", "description": "Mettre à jour un rôle"},
    {"name": "role:delete", "description": "Supprimer un rôle"},
    {"name": "role:assign_permission", "description": "Assigner une permission à un rôle"},
    # Permissions pour les permissions (lecture seule)
    {"name": "permission:read", "description": "Lire les permissions"},
    # Permissions pour les pointages
    {"name": "attendance:create", "description": "Créer un pointage"},
    {"name": "attendance:read", "description": "Lire les pointages"},
]

# Définition des rôles et des permissions qui leur sont associées
ROLES = {
    "Administrateur système": {
        "description": "Accès complet à toutes les fonctionnalités du système.",
        "permissions": [p["name"] for p in PERMISSIONS], # Toutes les permissions
    },
    "Manager / Responsable RH": {
        "description": "Gère les équipes, valide les absences et consulte les rapports.",
        "permissions": [
            "department:read",
            "attendance:read",
            "attendance:create", # Pour les pointages manuels
        ],
    },
    "Employé / Étudiant": {
        "description": "Peut pointer et consulter son historique personnel.",
        "permissions": [
            "attendance:read", # Logique métier à affiner pour ne voir que les siens
            "attendance:create", # Pour pointer
        ],
    },
}

async def seed_data():
    print("Début du seeding des rôles et permissions...")
    db: Session = next(SessionLocal.get_db())

    try:
        # 1. Créer toutes les permissions
        created_permissions = {}
        for perm_data in PERMISSIONS:
            permission = crud_permission.get_by_name(db, name=perm_data["name"])
            if not permission:
                permission = crud_permission.create(db, obj_in=PermissionCreate(**perm_data))
                print(f"Permission créée : {permission.name}")
            created_permissions[permission.name] = permission

        # 2. Créer les rôles et assigner les permissions
        for role_name, role_data in ROLES.items():
            role = crud_role.get_by_name(db, name=role_name)
            if not role:
                role = crud_role.create(db, obj_in=RoleCreate(name=role_name, description=role_data["description"]))
                print(f"Rôle créé : {role.name}")

            # Assigner les permissions au rôle
            permissions_to_assign = [
                created_permissions[perm_name] for perm_name in role_data["permissions"]
                if perm_name in created_permissions and created_permissions[perm_name] not in role.permissions
            ]
            if permissions_to_assign:
                crud_role.assign_permissions_to_role(db, role=role, permissions=permissions_to_assign)
                print(f"Permissions assignées à {role.name}: {[p.name for p in permissions_to_assign]}")

    finally:
        db.close()

    print("Seeding terminé.")

if __name__ == "__main__":
    asyncio.run(seed_data())
