from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.dependencies import get_db, get_current_active_user, PermissionChecker

router = APIRouter()

@router.get(
    "/",
    response_model=schemas.PaginatedResponse[schemas.User],
    summary="Lister tous les utilisateurs",
    description="Récupère une liste paginée de tous les utilisateurs. **Requiert la permission 'user:read'.**",
    dependencies=[Depends(PermissionChecker(["user:read"]))],
)
def read_users(
    db: Session = Depends(get_db),
    skip: int = Query(0, description="Nombre d'utilisateurs à sauter"),
    limit: int = Query(100, description="Nombre maximum d'utilisateurs à retourner"),
    include_inactive: bool = Query(False, description="Inclure les utilisateurs inactifs dans les résultats"),
) -> Any:
    """
    Retrieve users.
    """
    user_data = crud.user.get_multi(db, skip=skip, limit=limit, include_inactive=include_inactive)
    return {
        "items": user_data["items"],
        "total": user_data["total"],
        "skip": skip,
        "limit": limit,
    }

@router.post(
    "/",
    response_model=schemas.User,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouvel utilisateur",
    description="Crée un nouvel utilisateur dans le système. **Requiert la permission 'user:create'.**",
    dependencies=[Depends(PermissionChecker(["user:create"]))],
)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà.",
        )
    user = crud.user.create(db=db, obj_in=user_in)
    # Note: Role assignment should happen via the /roles/{role_id}/users/{user_id} endpoint.
    from app.utils.email import send_new_user_email
    token = crud.user.set_password_reset_token(db=db, user=user)
    send_new_user_email(to_email=user.email, token=token)
    return user

@router.get(
    "/{user_id}",
    response_model=schemas.User,
    summary="Lire un utilisateur par ID",
    dependencies=[Depends(PermissionChecker(["user:read"]))],
)
def read_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
) -> Any:
    """
    Get user by ID.
    """
    user = crud.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    return user

@router.put(
    "/{user_id}",
    response_model=schemas.User,
    summary="Mettre à jour un utilisateur",
    dependencies=[Depends(PermissionChecker(["user:update"]))],
)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    user_in: schemas.UserUpdate,
) -> Any:
    """
    Update a user.
    """
    user = crud.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    user = crud.user.update(db=db, db_obj=user, obj_in=user_in)
    return user

@router.post(
    "/{user_id}/deactivate",
    response_model=schemas.User,
    summary="Désactiver un utilisateur",
    dependencies=[Depends(PermissionChecker(["user:deactivate"]))],
)
def deactivate_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
) -> Any:
    """
    Deactivate a user.
    """
    user = crud.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    user_update = schemas.UserUpdate(is_active=False)
    user = crud.user.update(db=db, db_obj=user, obj_in=user_update)
    return user


@router.post(
    "/{user_id}/activate",
    response_model=schemas.User,
    summary="Activer un utilisateur",
    dependencies=[Depends(PermissionChecker(["user:activate"]))],
)
def activate_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
) -> Any:
    """
    Activate a user.
    """
    user = crud.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    user_update = schemas.UserUpdate(is_active=True)
    user = crud.user.update(db=db, db_obj=user, obj_in=user_update)
    return user

@router.post(
    "/{user_id}/roles/{role_id}",
    response_model=schemas.User,
    summary="Assigner un rôle à un utilisateur",
    dependencies=[Depends(PermissionChecker(["user:assign_role"]))],
)
def assign_role_to_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    role_id: str,
) -> Any:
    """
    Assign a role to a user.
    """
    user = crud.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

    role = crud.role.get(db=db, id=role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle non trouvé")

    user = crud.user.assign_role(db=db, user=user, role=role)
    return user
