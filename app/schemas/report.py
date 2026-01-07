from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import date as date_type
from enum import Enum


class ReportFormat(str, Enum):
    """Format de rapport disponible."""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class ReportPeriod(str, Enum):
    """Période de rapport disponible."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ReportRequest(BaseModel):
    """Requête de génération de rapport."""
    organization_id: int = Field(..., description="ID de l'organisation")
    period: ReportPeriod = Field(..., description="Période du rapport (daily, weekly, monthly, custom)")
    start_date: date_type = Field(..., description="Date de début du rapport")
    end_date: date_type = Field(..., description="Date de fin du rapport")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export (pdf, excel, csv)")
    employee_ids: Optional[List[int]] = Field(None, description="IDs des employés à inclure (optionnel)")
    department: Optional[str] = Field(None, description="Département à filtrer (optionnel)")
    include_charts: bool = Field(True, description="Inclure les graphiques dans le rapport")


class AttendanceReportRow(BaseModel):
    """Ligne de données pour un rapport de présence."""
    employee_id: UUID = Field(..., description="ID de l'employé")
    employee_name: str = Field(..., description="Nom complet de l'employé")
    badge_id: str = Field(..., description="Badge ID de l'employé")
    department: Optional[str] = Field(None, description="Département de l'employé")
    total_days: int = Field(..., description="Nombre total de jours dans la période")
    present_days: int = Field(..., description="Nombre de jours de présence")
    absent_days: int = Field(..., description="Nombre de jours d'absence")
    late_days: int = Field(..., description="Nombre de jours avec retard")
    on_leave_days: int = Field(..., description="Nombre de jours de congé")
    attendance_rate: float = Field(..., description="Taux de présence en pourcentage")
    total_hours: float = Field(..., description="Total d'heures travaillées")


class AttendanceReport(BaseModel):
    """Rapport de présence complet."""
    organization_name: str = Field(..., description="Nom de l'organisation")
    period: str = Field(..., description="Période du rapport (ex: 'Janvier 2024')")
    start_date: date_type = Field(..., description="Date de début")
    end_date: date_type = Field(..., description="Date de fin")
    total_employees: int = Field(..., description="Nombre total d'employés dans le rapport")
    rows: List[AttendanceReportRow] = Field(..., description="Données par employé")
    summary: dict = Field(..., description="Résumé statistique du rapport")


class EmployeeDetailReport(BaseModel):
    """Rapport détaillé d'un employé."""
    employee_id: UUID = Field(..., description="ID de l'employé")
    employee_name: str = Field(..., description="Nom complet de l'employé")
    badge_id: str = Field(..., description="Badge ID de l'employé")
    department: Optional[str] = Field(None, description="Département de l'employé")
    period: str = Field(..., description="Période du rapport")
    total_check_ins: int = Field(..., description="Nombre total d'entrées")
    total_check_outs: int = Field(..., description="Nombre total de sorties")
    average_arrival_time: Optional[str] = Field(None, description="Heure moyenne d'arrivée")
    average_departure_time: Optional[str] = Field(None, description="Heure moyenne de départ")
    late_arrivals: int = Field(..., description="Nombre d'arrivées en retard")
    early_departures: int = Field(..., description="Nombre de départs anticipés")
    total_hours: float = Field(..., description="Total d'heures travaillées")
    attendance_rate: float = Field(..., description="Taux de présence en pourcentage")


class EmployeePresenceReportRequest(BaseModel):
    """Requête pour R17 - Rapport de présence employé."""
    start_date: date_type = Field(..., description="Date de début de la période")
    end_date: date_type = Field(..., description="Date de fin de la période")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")
    detailed: bool = Field(False, description="Inclure les détails horaires")


class EmployeePresenceReportRow(BaseModel):
    """Ligne de données pour R17."""
    date: date_type = Field(..., description="Date du jour")
    check_in: Optional[str] = Field(None, description="Heure d'entrée")
    check_out: Optional[str] = Field(None, description="Heure de sortie")
    total_hours: Optional[float] = Field(None, description="Heures travaillées")
    status: str = Field(..., description="Statut du jour (Present, Absent, On Leave)")


class EmployeePresenceReportResponse(BaseModel):
    """Réponse pour R17 - Aperçu du rapport."""
    employee_name: str = Field(..., description="Nom de l'employé")
    employee_badge_id: str = Field(..., description="Badge ID de l'employé")
    department_name: Optional[str] = Field(None, description="Département")
    start_date: date_type = Field(..., description="Date de début")
    end_date: date_type = Field(..., description="Date de fin")
    data: List[EmployeePresenceReportRow] = Field(..., description="Données journalières")
    summary: Dict[str, Any] = Field(..., description="Résumé statistique")


class EmployeeMonthlySummaryRequest(BaseModel):
    """Requête pour R18 - Synthèse mensuelle employé."""
    year: int = Field(..., description="Année")
    month: int = Field(..., description="Mois (1-12)")
    include_charts: bool = Field(True, description="Inclure les données pour graphiques")


class EmployeeMonthlySummaryResponse(BaseModel):
    """Réponse pour R18 - Synthèse mensuelle."""
    employee_name: str = Field(..., description="Nom de l'employé")
    employee_badge_id: str = Field(..., description="Badge ID de l'employé")
    department_name: Optional[str] = Field(None, description="Département")
    period: str = Field(..., description="Période (ex: 'Janvier 2024')")
    summary: Dict[str, Any] = Field(..., description="Statistiques mensuelles")
    daily_data: List[Dict[str, Any]] = Field(..., description="Données journalières pour graphiques")


from app.models.leave import LeaveStatus, LeaveType

class EmployeeLeavesReportRequest(BaseModel):
    """Requête pour R19 - Rapport des congés employé."""
    year: int = Field(..., description="Année du rapport")
    leave_type: Optional[LeaveType] = Field(None, description="Type de congé à filtrer")
    status: Optional[LeaveStatus] = Field(None, description="Statut des congés à filtrer")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")


class EmployeeLeaveReportRow(BaseModel):
    """Ligne de données pour R19."""
    start_date: date_type = Field(..., description="Date de début du congé")
    end_date: date_type = Field(..., description="Date de fin du congé")
    leave_type: str = Field(..., description="Type de congé")
    status: str = Field(..., description="Statut du congé")
    reason: str = Field(..., description="Motif du congé")
    total_days: int = Field(..., description="Nombre de jours")

    class Config:
        from_attributes = True


class EmployeeLeavesReportResponse(BaseModel):
    """Réponse pour R19 - Aperçu des congés."""
    employee_name: str = Field(..., description="Nom de l'employé")
    year: int = Field(..., description="Année du rapport")
    data: List[EmployeeLeaveReportRow] = Field(..., description="Liste des congés")
    summary: Dict[str, int] = Field(..., description="Résumé par type de congé")


class PresenceCertificateRequest(BaseModel):
    """Requête pour R20 - Attestation de présence."""
    start_date: date_type = Field(..., description="Date de début de la période")
    end_date: date_type = Field(..., description="Date de fin de la période")


# Schemas for Manager Reports (Phase 2)

class DepartmentPresenceRequest(BaseModel):
    """Requête pour R12 - Rapport présence département."""
    start_date: date_type = Field(..., description="Date de début")
    end_date: date_type = Field(..., description="Date de fin")
    employee_ids: Optional[List[str]] = Field(None, description="IDs employés à filtrer")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")
    grouping: str = Field("daily", description="Groupement (daily, weekly)")


class DepartmentPresenceReportRow(BaseModel):
    """Ligne de données pour R12."""
    employee_id: str = Field(..., description="ID de l'employé")
    employee_name: str = Field(..., description="Nom de l'employé")
    present_days: int = Field(..., description="Jours de présence")
    absent_days: int = Field(..., description="Jours d'absence")
    on_leave_days: int = Field(..., description="Jours de congé")
    total_hours_worked: float = Field(..., description="Total heures travaillées")


class DepartmentPresenceResponse(BaseModel):
    """Réponse pour R12."""
    department_name: str = Field(..., description="Nom du département")
    period: str = Field(..., description="Période du rapport")
    data: List[DepartmentPresenceReportRow] = Field(..., description="Données par employé")
    summary: Dict[str, Any] = Field(..., description="Résumé statistique")


class TeamWeeklyReportRequest(BaseModel):
    """Requête pour R13 - Rapport hebdomadaire équipe."""
    year: int = Field(..., description="Année")
    week_number: int = Field(..., description="Numéro de semaine (1-53)")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")
    detailed: bool = Field(False, description="Mode détaillé vs synthèse")


class DepartmentLeavesRequest(BaseModel):
    """Requête pour R15 - Congés département."""
    start_date: date_type = Field(..., description="Date de début")
    end_date: date_type = Field(..., description="Date de fin")
    leave_type: Optional[LeaveType] = Field(None, description="Type de congé à filtrer")
    status: Optional[LeaveStatus] = Field(None, description="Statut à filtrer")
    employee_ids: Optional[List[str]] = Field(None, description="IDs employés à filtrer")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")


class DepartmentLeaveReportRow(BaseModel):
    """Ligne de données pour R15."""
    employee_name: str = Field(..., description="Nom de l'employé")
    start_date: date_type = Field(..., description="Date de début")
    end_date: date_type = Field(..., description="Date de fin")
    leave_type: str = Field(..., description="Type de congé")
    status: str = Field(..., description="Statut du congé")
    reason: str = Field(..., description="Motif")
    total_days: int = Field(..., description="Nombre de jours")


class DepartmentLeavesResponse(BaseModel):
    """Réponse pour R15."""
    department_name: str = Field(..., description="Nom du département")
    period: str = Field(..., description="Période")
    data: List[DepartmentLeaveReportRow] = Field(..., description="Liste des congés")


class TeamPerformanceRequest(BaseModel):
    """Requête pour R16 - Performance équipe."""
    year: int = Field(..., description="Année")
    month: Optional[int] = Field(None, description="Mois (1-12)")
    quarter: Optional[int] = Field(None, description="Trimestre (1-4)")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")


class TeamPerformanceRow(BaseModel):
    """Ligne de données pour R16."""
    employee_id: str = Field(..., description="ID de l'employé")
    employee_name: str = Field(..., description="Nom de l'employé")
    attendance_rate: float = Field(..., description="Taux de présence (%)")
    total_hours_worked: float = Field(..., description="Heures travaillées")


class TeamPerformanceResponse(BaseModel):
    """Réponse pour R16."""
    department_name: str = Field(..., description="Nom du département")
    period: str = Field(..., description="Période")
    data: List[TeamPerformanceRow] = Field(..., description="Données par employé")


class HoursValidationRequest(BaseModel):
    """Requête pour R14 - Validation des heures."""
    year: int = Field(..., description="Année")
    month: int = Field(..., description="Mois (1-12)")
    employee_ids: Optional[List[str]] = Field(None, description="IDs employés à filtrer")
    validation_status: Optional[str] = Field("pending", description="Statut (pending, validated)")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")


class HoursValidationRow(BaseModel):
    """Ligne de données pour R14."""
    employee_name: str = Field(..., description="Nom de l'employé")
    total_hours_worked: float = Field(..., description="Heures travaillées")
    total_hours_to_validate: float = Field(..., description="Heures à valider")
    status: str = Field(..., description="Statut de validation")


class HoursValidationResponse(BaseModel):
    """Réponse pour R14."""
    department_name: str = Field(..., description="Nom du département")
    period: str = Field(..., description="Période")
    data: List[HoursValidationRow] = Field(..., description="Données par employé")


# Schemas for HR / Org Admin Reports (Phase 3)

class OrganizationPresenceRequest(BaseModel):
    """Requête pour R5 - Présence organisation."""
    start_date: date_type = Field(..., description="Date de début")
    end_date: date_type = Field(..., description="Date de fin")
    site_ids: Optional[List[str]] = Field(None, description="IDs sites à filtrer")
    department_ids: Optional[List[str]] = Field(None, description="IDs départements à filtrer")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")


class OrganizationPresenceResponse(BaseModel):
    """Réponse pour R5."""
    organization_name: str = Field(..., description="Nom de l'organisation")
    period: str = Field(..., description="Période")
    data: List[DepartmentPresenceReportRow] = Field(..., description="Données par employé")
    summary: Dict[str, Any] = Field(..., description="Résumé statistique")


class MonthlySyntheticReportRequest(BaseModel):
    """Requête pour R6 - Synthèse mensuelle."""
    year: int = Field(..., description="Année")
    month: int = Field(..., description="Mois (1-12)")
    site_ids: Optional[List[str]] = Field(None, description="IDs sites à filtrer")
    department_ids: Optional[List[str]] = Field(None, description="IDs départements à filtrer")
    include_overtime: bool = Field(True, description="Inclure les heures supplémentaires")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")


class OrganizationLeavesRequest(BaseModel):
    """Requête pour R7 - Analyse congés organisation."""
    start_date: date_type = Field(..., description="Date de début")
    end_date: date_type = Field(..., description="Date de fin")
    leave_type: Optional[LeaveType] = Field(None, description="Type de congé à filtrer")
    status: Optional[LeaveStatus] = Field(None, description="Statut à filtrer")
    department_ids: Optional[List[str]] = Field(None, description="IDs départements à filtrer")
    employee_ids: Optional[List[str]] = Field(None, description="IDs employés à filtrer")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")


class WorkedHoursRequest(BaseModel):
    """Requête pour R9 - Heures travaillées par employé."""
    start_date: date_type = Field(..., description="Date de début")
    end_date: date_type = Field(..., description="Date de fin")
    department_ids: Optional[List[str]] = Field(None, description="IDs départements à filtrer")
    employee_ids: Optional[List[str]] = Field(None, description="IDs employés à filtrer")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")


class WorkedHoursRow(BaseModel):
    """Ligne de données pour R9."""
    employee_name: str = Field(..., description="Nom de l'employé")
    department_name: Optional[str] = Field(None, description="Département")
    date: date_type = Field(..., description="Date")
    status: str = Field(..., description="Statut du jour")
    check_in: Optional[str] = Field(None, description="Heure d'entrée")
    check_out: Optional[str] = Field(None, description="Heure de sortie")
    total_hours: float = Field(..., description="Heures travaillées")


class WorkedHoursResponse(BaseModel):
    """Réponse pour R9."""
    organization_name: str = Field(..., description="Nom de l'organisation")
    period: str = Field(..., description="Période")
    data: List[WorkedHoursRow] = Field(..., description="Données journalières")


class SiteActivityRequest(BaseModel):
    """Requête pour R10 - Activité par site."""
    start_date: date_type = Field(..., description="Date de début")
    end_date: date_type = Field(..., description="Date de fin")
    site_ids: List[str] = Field(..., description="IDs des sites")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")
    detailed: bool = Field(False, description="Mode détaillé")


class SiteActivityRow(BaseModel):
    """Ligne de données pour R10."""
    site_name: str = Field(..., description="Nom du site")
    total_employees: int = Field(..., description="Total employés")
    present_employees: int = Field(..., description="Employés présents")
    on_leave_employees: int = Field(..., description="Employés en congé")
    total_hours_worked: float = Field(..., description="Total heures travaillées")
    average_hours_per_employee: float = Field(..., description="Moyenne heures/employé")


class SiteActivityResponse(BaseModel):
    """Réponse pour R10."""
    organization_name: str = Field(..., description="Nom de l'organisation")
    period: str = Field(..., description="Période")
    data: List[SiteActivityRow] = Field(..., description="Données par site")


class AnomaliesReportRequest(BaseModel):
    """Requête pour R8 - Rapport des anomalies."""
    start_date: date_type = Field(..., description="Date de début")
    end_date: date_type = Field(..., description="Date de fin")
    site_ids: Optional[List[str]] = Field(None, description="IDs sites à filtrer")
    department_ids: Optional[List[str]] = Field(None, description="IDs départements à filtrer")
    tardiness_threshold: int = Field(5, description="Seuil de retard en minutes")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")


class AnomaliesReportRow(BaseModel):
    """Ligne de données pour R8."""
    employee_name: str = Field(..., description="Nom de l'employé")
    department_name: Optional[str] = Field(None, description="Département")
    date: date_type = Field(..., description="Date de l'anomalie")
    anomaly_type: str = Field(..., description="Type d'anomalie (Late Arrival, Missing Check-out)")
    details: str = Field(..., description="Détails de l'anomalie")


class AnomaliesReportResponse(BaseModel):
    """Réponse pour R8."""
    organization_name: str = Field(..., description="Nom de l'organisation")
    period: str = Field(..., description="Période")
    data: List[AnomaliesReportRow] = Field(..., description="Liste des anomalies")


class PayrollExportRequest(BaseModel):
    """Requête pour R11 - Export paie."""
    year: int = Field(..., description="Année")
    month: int = Field(..., description="Mois (1-12)")
    site_ids: Optional[List[str]] = Field(None, description="IDs sites à filtrer")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")


class PayrollExportRow(BaseModel):
    """Ligne de données pour R11."""
    employee_id: str = Field(..., description="ID de l'employé")
    employee_name: str = Field(..., description="Nom de l'employé")
    total_hours_worked: float = Field(..., description="Heures travaillées")
    overtime_hours: float = Field(..., description="Heures supplémentaires")
    leave_days: int = Field(..., description="Jours de congé")


class PayrollExportResponse(BaseModel):
    """Réponse pour R11 - Téléchargement direct."""
    filename: str = Field(..., description="Nom du fichier généré")
    content: str = Field(..., description="Contenu encodé en base64")


# Schemas for Super Admin Reports (Phase 4)

class MultiOrgConsolidatedRequest(BaseModel):
    """Requête pour R1 - Rapport consolidé multi-organisations."""
    start_date: date_type = Field(..., description="Date de début")
    end_date: date_type = Field(..., description="Date de fin")
    organization_ids: Optional[List[str]] = Field(None, description="IDs organisations à inclure")
    metric_type: str = Field(..., description="Type de métrique (presence, leaves, delays)")
    grouping: str = Field(..., description="Groupement (daily, weekly, monthly)")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")


class MultiOrgConsolidatedRow(BaseModel):
    """Ligne de données pour R1."""
    organization_name: str = Field(..., description="Nom de l'organisation")
    present_days: int = Field(..., description="Jours de présence")
    on_leave_days: int = Field(..., description="Jours de congé")
    total_hours_worked: float = Field(..., description="Heures travaillées")


class MultiOrgConsolidatedResponse(BaseModel):
    """Réponse pour R1."""
    period: str = Field(..., description="Période du rapport")
    data: List[MultiOrgConsolidatedRow] = Field(..., description="Données par organisation")


class ComparativeAnalysisRequest(BaseModel):
    """Requête pour R2 - Analyse comparative."""
    year: int = Field(..., description="Année")
    month: Optional[int] = Field(None, description="Mois (1-12)")
    quarter: Optional[int] = Field(None, description="Trimestre (1-4)")
    organization_ids: List[str] = Field(..., description="IDs organisations à comparer")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")


class ComparativeAnalysisRow(BaseModel):
    """Ligne de données pour R2."""
    organization_name: str = Field(..., description="Nom de l'organisation")
    attendance_rate: float = Field(..., description="Taux de présence (%)")
    total_hours_worked: float = Field(..., description="Heures travaillées")
    total_leave_days: int = Field(..., description="Jours de congé")


class ComparativeAnalysisResponse(BaseModel):
    """Réponse pour R2."""
    period: str = Field(..., description="Période")
    data: List[ComparativeAnalysisRow] = Field(..., description="Données comparatives")


class DeviceUsageRequest(BaseModel):
    """Requête pour R3 - Utilisation des terminaux."""
    start_date: date_type = Field(..., description="Date de début")
    end_date: date_type = Field(..., description="Date de fin")
    organization_ids: Optional[List[str]] = Field(None, description="IDs organisations")
    site_ids: Optional[List[str]] = Field(None, description="IDs sites")
    status: Optional[str] = Field(None, description="Statut (Online, Offline, Maintenance)")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")


class DeviceUsageRow(BaseModel):
    """Ligne de données pour R3."""
    device_name: str = Field(..., description="Nom du terminal")
    device_serial_number: str = Field(..., description="Numéro de série")
    site_name: Optional[str] = Field(None, description="Site d'installation")
    organization_name: str = Field(..., description="Organisation propriétaire")
    status: str = Field(..., description="Statut actuel")
    last_ping: Optional[str] = Field(None, description="Dernier ping reçu")


class DeviceUsageResponse(BaseModel):
    """Réponse pour R3."""
    period: str = Field(..., description="Période")
    data: List[DeviceUsageRow] = Field(..., description="Données des terminaux")


class UserAuditRequest(BaseModel):
    """Requête pour R4 - Audit utilisateurs et rôles."""
    organization_ids: Optional[List[str]] = Field(None, description="IDs organisations")
    role_ids: Optional[List[str]] = Field(None, description="IDs rôles")
    is_active: Optional[bool] = Field(None, description="Filtrer par statut actif")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format d'export")


class UserAuditRow(BaseModel):
    """Ligne de données pour R4."""
    full_name: str = Field(..., description="Nom complet")
    email: str = Field(..., description="Email")
    role: str = Field(..., description="Rôle principal")
    organization_name: str = Field(..., description="Organisation")
    is_active: bool = Field(..., description="Compte actif")
    last_login: Optional[str] = Field(None, description="Dernière connexion")


class UserAuditResponse(BaseModel):
    """Réponse pour R4."""
    filters: Dict[str, Any] = Field(..., description="Filtres appliqués")
    user_count: int = Field(..., description="Nombre d'utilisateurs")
    data: List[UserAuditRow] = Field(..., description="Liste des utilisateurs")