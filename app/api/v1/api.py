from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    employees,
    attendance,
    organizations,
    devices,
    reports,
    departments,
    roles,
    permissions,
    ws,
    sites,
    leaves,
    dashboard,
)

# Router principal v1
api_router = APIRouter()

# Inclure les routes de chaque module
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentification"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Utilisateurs"]
)

api_router.include_router(
    organizations.router,
    prefix="/organizations",
    tags=["Organisations"]
)

api_router.include_router(
    employees.router,
    prefix="/employees",
    tags=["Employés"]
)

api_router.include_router(
    devices.router,
    prefix="/devices",
    tags=["Devices IoT"]
)

api_router.include_router(
    attendance.router,
    prefix="/attendance",
    tags=["Pointages"]
)

api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Rapports"]
)

api_router.include_router(
    departments.router,
    prefix="/departments",
    tags=["Départements"]
)

api_router.include_router(
    roles.router,
    prefix="/roles",
    tags=["Rôles & Permissions"]
)

api_router.include_router(
    permissions.router,
    prefix="/permissions",
    tags=["Rôles & Permissions"]
)

api_router.include_router(
    ws.router,
    prefix="",
    tags=["WebSockets"]
)

api_router.include_router(
    sites.router,
    prefix="/sites",
    tags=["Sites"]
)

api_router.include_router(
    leaves.router,
    prefix="/leaves",
    tags=["Leaves"]
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"]
)