from pydantic import BaseModel, Field
from typing import List, Dict

# System Administrator Schemas
class UsersPerOrg(BaseModel):
    name: str = Field(..., description="Nom de l'organisation")
    user_count: int = Field(..., description="Nombre d'utilisateurs dans l'organisation")

class SitesPerOrg(BaseModel):
    name: str = Field(..., description="Nom de l'organisation")
    site_count: int = Field(..., description="Nombre de sites dans l'organisation")

class DeviceStatusRatio(BaseModel):
    status: str = Field(..., description="Statut du terminal (online, offline, maintenance)")
    count: int = Field(..., description="Nombre de terminaux avec ce statut")

class PlanDistribution(BaseModel):
    plan: str = Field(..., description="Type de plan d'abonnement")
    count: int = Field(..., description="Nombre d'organisations avec ce plan")

class Top10Organizations(BaseModel):
    name: str = Field(..., description="Nom de l'organisation")
    employee_count: int = Field(..., description="Nombre d'employés")

class AdminDashboard(BaseModel):
    """Tableau de bord pour les administrateurs système."""
    active_organizations: int = Field(..., description="Nombre d'organisations actives")
    users_per_organization: List[UsersPerOrg] = Field(..., description="Répartition des utilisateurs par organisation")
    sites_per_organization: List[SitesPerOrg] = Field(..., description="Répartition des sites par organisation")
    device_status_ratio: List[DeviceStatusRatio] = Field(..., description="Ratio des statuts des terminaux")
    daily_attendance_count: int = Field(..., description="Nombre total de pointages du jour")
    plan_distribution: List[PlanDistribution] = Field(..., description="Distribution des plans d'abonnement")
    top_10_organizations_by_employees: List[Top10Organizations] = Field(..., description="Top 10 des organisations par nombre d'employés")

# Manager/HR Schemas
from .attendance import Attendance

from datetime import date as date_type

class PresenceEvolution(BaseModel):
    date: date_type = Field(..., description="Date du jour")
    presence_count: int = Field(..., description="Nombre de présences ce jour")

class PresenceAbsenceTardinessDistribution(BaseModel):
    present: int = Field(..., description="Nombre d'employés présents")
    absent: int = Field(..., description="Nombre d'employés absents")
    tardy: int = Field(..., description="Nombre d'employés en retard")

class ManagerDashboard(BaseModel):
    """Tableau de bord pour les managers et RH."""
    present_today: int = Field(..., description="Nombre d'employés présents aujourd'hui")
    absent_today: int = Field(..., description="Nombre d'employés absents aujourd'hui")
    tardy_today: int = Field(..., description="Nombre d'employés en retard aujourd'hui")
    attendance_rate: float = Field(..., description="Taux de présence en pourcentage")
    total_work_hours: float = Field(..., description="Nombre total d'heures travaillées")
    pending_leaves: int = Field(..., description="Nombre de demandes de congés en attente")
    presence_evolution: List[PresenceEvolution] = Field(..., description="Évolution des présences sur la période")
    presence_absence_tardiness_distribution: PresenceAbsenceTardinessDistribution = Field(..., description="Distribution présences/absences/retards")
    real_time_attendances: List[Attendance] = Field(..., description="Derniers pointages en temps réel")

# Employee Schemas
class LeaveBalance(BaseModel):
    total: int = Field(..., description="Nombre total de jours de congés")
    used: int = Field(..., description="Nombre de jours utilisés")
    available: int = Field(..., description="Nombre de jours disponibles")

class EmployeeDashboard(BaseModel):
    """Tableau de bord pour les employés."""
    today_attendances: List[Attendance] = Field(..., description="Pointages du jour de l'employé")
    monthly_attendance_rate: float = Field(..., description="Taux de présence mensuel en pourcentage")
    leave_balance: LeaveBalance = Field(..., description="Solde des congés")

# Integrator/IoT Technician Schemas
class AttendancePerDevice(BaseModel):
    serial_number: str = Field(..., description="Numéro de série du terminal")
    attendance_count: int = Field(..., description="Nombre de pointages enregistrés")

class IntegratorDashboard(BaseModel):
    """Tableau de bord pour les intégrateurs/techniciens IoT."""
    device_status_ratio: List[DeviceStatusRatio] = Field(..., description="Ratio des statuts des terminaux")
    attendance_per_device: List[AttendancePerDevice] = Field(..., description="Pointages par terminal")

# Advanced Analytics Schemas
class TardinessByDay(BaseModel):
    day: str = Field(..., description="Jour de la semaine (ex: 'Lundi', 'Mardi')")
    tardy_count: int = Field(..., description="Nombre de retards ce jour")

class AdvancedAnalytics(BaseModel):
    """Analyses avancées pour les statistiques."""
    tardiness_by_day_of_week: List[TardinessByDay] = Field(..., description="Retards par jour de la semaine")