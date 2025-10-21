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
    # Permissions pour les utilisateurs
    {"name": "user:create", "description": "Créer un utilisateur"},
    {"name": "user:read", "description": "Lire les utilisateurs"},
    {"name": "user:update", "description": "Mettre à jour un utilisateur"},
    {"name": "user:assign_role", "description": "Assigner un rôle à un utilisateur"},
    {"name": "user:activate", "description": "Activer un utilisateur"},
    {"name": "user:deactivate", "description": "Désactiver un utilisateur"},
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
    # Permissions pour les rapports
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
            "report:R5:view",
            "report:R6:view",
            "report:R7:view",
            "report:R8:view",
            "report:R9:view",
            "report:R10:view",
            "report:R11:view",
        ],
    },
    "Manager de département": {
        "description": "Gère une équipe spécifique et accède aux rapports départementaux.",
        "permissions": [
            "department:read",
            "attendance:read",
            "report:R12:view",
            "report:R13:view",
            "report:R14:view",
            "report:R15:view",
            "report:R16:view",
        ],
    },
    "Employé / Étudiant": {
        "description": "Peut pointer et consulter son historique personnel.",
        "permissions": [
            "attendance:read", # Logique métier à affiner pour ne voir que les siens
            "attendance:create", # Pour pointer
            "report:R17:view",
            "report:R18:view",
            "report:R19:view",
            "report:R20:view",
        ],
    },
}

async def seed_data():
    print("Début du seeding des rôles et permissions...")
    db: Session = SessionLocal()

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
