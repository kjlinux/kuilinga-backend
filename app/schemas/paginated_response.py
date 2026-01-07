from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Réponse paginée générique pour les listes d'éléments."""
    items: List[T] = Field(..., description="Liste des éléments de la page courante")
    total: int = Field(..., description="Nombre total d'éléments disponibles")
    skip: int = Field(..., description="Nombre d'éléments sautés (offset)")
    limit: int = Field(..., description="Nombre maximum d'éléments par page")