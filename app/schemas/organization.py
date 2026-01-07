from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any


def parse_bool_field(value: Any) -> bool:
    """Convert string values like 'Active'/'Inactive' to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("active", "true", "1", "yes", "oui", "actif")
    return bool(value)


# Schéma de base pour l'organisation
class OrganizationBase(BaseModel):
    name: str = Field(..., example="Tanga Group", description="Nom de l'organisation")
    description: Optional[str] = Field(None, example="Société de technologie", description="Description de l'organisation")
    email: Optional[str] = Field(None, example="contact@tangagroup.com", description="Adresse email de contact")
    phone: Optional[str] = Field(None, example="+225 0102030405", description="Numéro de téléphone de contact")
    timezone: str = Field("Africa/Abidjan", example="Africa/Abidjan", description="Fuseau horaire (ex: 'Africa/Abidjan', 'Europe/Paris')")
    plan: Optional[str] = Field("standard", example="premium", description="Plan d'abonnement (standard, premium, enterprise)")
    is_active: bool = Field(True, description="Indique si l'organisation est active")

    @field_validator("is_active", mode="before")
    @classmethod
    def validate_is_active(cls, v: Any) -> bool:
        return parse_bool_field(v)


# Schéma pour la création d'une organisation
class OrganizationCreate(OrganizationBase):
    pass

# Schéma pour la mise à jour d'une organisation
class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Nom de l'organisation")
    description: Optional[str] = Field(None, description="Description de l'organisation")
    email: Optional[str] = Field(None, description="Adresse email de contact")
    phone: Optional[str] = Field(None, description="Numéro de téléphone de contact")
    timezone: Optional[str] = Field(None, description="Fuseau horaire")
    plan: Optional[str] = Field(None, description="Plan d'abonnement")
    is_active: Optional[bool] = Field(None, description="Indique si l'organisation est active")

    @field_validator("is_active", mode="before")
    @classmethod
    def validate_is_active(cls, v: Any) -> Optional[bool]:
        if v is None:
            return None
        return parse_bool_field(v)

# Schéma complet pour retourner via l'API
class Organization(OrganizationBase):
    id: str = Field(..., description="Identifiant unique de l'organisation")
    sites_count: int = Field(0, description="Nombre de sites dans l'organisation")
    employees_count: int = Field(0, description="Nombre d'employés dans l'organisation")
    users_count: int = Field(0, description="Nombre d'utilisateurs dans l'organisation")

    class Config:
        from_attributes = True