from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.dependencies import get_db, get_current_active_user, require_role
from app.models.user import UserRole

router = APIRouter()

@router.get(
    "/",
    response_model=List[schemas.User],
    summary="Lister tous les utilisateurs",
    description="Récupère une liste paginée de tous les utilisateurs. **Requiert le rôle 'admin'.**",
)
def read_users(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Nombre d'utilisateurs à sauter"),
    limit: int = Query(100, description="Nombre maximum d'utilisateurs à retourner"),
    current_user: models.User = Depends(require_role(UserRole.ADMIN)),
) -> Any:
    users = crud.user.get_multi(db, skip=skip, limit=limit)
    return users

@router.post(
    "/",
    response_model=schemas.User,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouvel utilisateur",
    description="Crée un nouvel utilisateur dans le système. **Requiert le rôle 'admin'.**",
    responses={
        400: {"description": "Un utilisateur avec cet email existe déjà"},
    },
)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(require_role(UserRole.ADMIN)),
) -> Any:
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà.",
        )
    user = crud.user.create(db=db, obj_in=user_in)
    return user

@router.get(
    "/{user_id}",
    response_model=schemas.User,
    summary="Lire un utilisateur par ID",
    description="Récupère les informations d'un utilisateur spécifique par son ID.",
    responses={
        403: {"description": "Permissions insuffisantes"},
        404: {"description": "Utilisateur non trouvé"},
    },
)
def read_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    user = crud.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

    if user.id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")

    return user

@router.put(
    "/{user_id}",
    response_model=schemas.User,
    summary="Mettre à jour un utilisateur",
    description="Met à jour les informations d'un utilisateur. Un utilisateur ne peut mettre à jour que ses propres informations, sauf un admin.",
    responses={
        403: {"description": "Permissions insuffisantes"},
        404: {"description": "Utilisateur non trouvé"},
    },
)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    user = crud.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

    if user.id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")

    user = crud.user.update(db=db, db_obj=user, obj_in=user_in)
    return user

@router.delete(
    "/{user_id}",
    response_model=schemas.User,
    summary="Supprimer un utilisateur",
    description="Supprime un utilisateur du système. **Requiert le rôle 'admin'.**",
    responses={
        403: {"description": "Permissions insuffisantes"},
        404: {"description": "Utilisateur non trouvé"},
    },
)
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    current_user: models.User = Depends(require_role(UserRole.ADMIN)),
) -> Any:
    user = crud.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

    deleted_user = crud.user.remove(db=db, id=user_id)
    return deleted_user