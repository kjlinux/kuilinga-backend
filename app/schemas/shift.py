from pydantic import BaseModel, Field
from typing import Optional
from datetime import time

# Propriétés partagées pour les shifts
class ShiftBase(BaseModel):
    name: str = Field(..., example="Journée de travail standard", description="Nom de l'horaire de travail")
    start_time: time = Field(..., example="09:00:00", description="Heure de début (format HH:MM:SS)")
    end_time: time = Field(..., example="17:00:00", description="Heure de fin (format HH:MM:SS)")
    organization_id: str = Field(..., description="ID de l'organisation propriétaire")

# Propriétés pour la création d'un shift
class ShiftCreate(ShiftBase):
    pass

# Propriétés pour la mise à jour d'un shift
class ShiftUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Nom de l'horaire de travail")
    start_time: Optional[time] = Field(None, description="Heure de début")
    end_time: Optional[time] = Field(None, description="Heure de fin")

# Propriétés à retourner via l'API
class Shift(ShiftBase):
    id: str = Field(..., description="Identifiant unique de l'horaire")

    class Config:
        from_attributes = True
