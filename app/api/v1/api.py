from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, employees, attendance, organizations, devices, reports

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