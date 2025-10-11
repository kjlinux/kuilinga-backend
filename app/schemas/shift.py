from pydantic import BaseModel, Field
from typing import Optional
from datetime import time

# Propriétés partagées pour les shifts
class ShiftBase(BaseModel):
    name: str = Field(..., example="Journée de travail standard")
    start_time: time = Field(..., example="09:00:00")
    end_time: time = Field(..., example="17:00:00")
    organization_id: str

# Propriétés pour la création d'un shift
class ShiftCreate(ShiftBase):
    pass

# Propriétés pour la mise à jour d'un shift
class ShiftUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

# Propriétés à retourner via l'API
class Shift(ShiftBase):
    id: str

    class Config:
        from_attributes = True
