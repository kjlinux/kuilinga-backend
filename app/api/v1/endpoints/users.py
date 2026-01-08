import os
import uuid
import shutil
from pathlib import Path
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.config import settings
from app.dependencies import get_db, get_current_active_user, PermissionChecker

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

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
    search: str = Query(None, description="Recherche textuelle (email, nom complet)"),
    sort_by: str = Query(None, description="Champ de tri (email, full_name, created_at, updated_at)"),
    sort_order: str = Query("asc", description="Direction du tri (asc ou desc)"),
) -> Any:
    """
    Retrieve users.
    """
    user_data = crud.user.get_multi_paginated(
        db,
        skip=skip,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
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

@router.delete(
    "/{user_id}",
    response_model=schemas.User,
    summary="Supprimer un utilisateur",
    dependencies=[Depends(PermissionChecker(["user:delete"]))],
)
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: str,
) -> Any:
    """
    Delete a user.
    """
    user = crud.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
    # Build response data while session is still active
    response_data = schemas.User.model_validate(user)
    crud.user.remove(db=db, id=user_id)
    return response_data

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


@router.post(
    "/{user_id}/avatar",
    response_model=schemas.AvatarUploadResponse,
    summary="Uploader une photo de profil",
    description="Upload une image de profil pour l'utilisateur. Formats acceptés: JPEG, PNG, GIF, WebP. Taille max: 10MB.",
)
def upload_avatar(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    current_user: models.User = Depends(get_current_active_user),
    file: UploadFile = File(..., description="Image de profil à uploader"),
) -> Any:
    """
    Upload a profile picture for a user.

    - L'utilisateur peut uploader son propre avatar
    - Les superusers peuvent uploader l'avatar de n'importe quel utilisateur
    """
    # Vérifier que l'utilisateur existe
    user = crud.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    # Vérifier les permissions: l'utilisateur peut modifier son propre avatar ou être superuser
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier l'avatar de cet utilisateur"
        )

    # Vérifier le type de fichier
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de fichier non autorisé. Types acceptés: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )

    # Vérifier l'extension du fichier
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extension de fichier non autorisée. Extensions acceptées: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Vérifier la taille du fichier
    file.file.seek(0, 2)  # Aller à la fin du fichier
    file_size = file.file.tell()
    file.file.seek(0)  # Revenir au début

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fichier trop volumineux. Taille max: {settings.MAX_UPLOAD_SIZE // (1024 * 1024)}MB"
        )

    # Créer le répertoire d'upload si nécessaire
    avatars_dir = Path(settings.UPLOAD_DIR) / "avatars"
    avatars_dir.mkdir(parents=True, exist_ok=True)

    # Supprimer l'ancien avatar si existant
    if user.avatar_url:
        old_avatar_path = Path(user.avatar_url.lstrip("/"))
        if old_avatar_path.exists():
            try:
                old_avatar_path.unlink()
            except OSError:
                pass  # Ignorer les erreurs de suppression

    # Générer un nom de fichier unique
    unique_filename = f"{user_id}_{uuid.uuid4().hex}{file_ext}"
    file_path = avatars_dir / unique_filename

    # Sauvegarder le fichier
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la sauvegarde du fichier"
        )

    # Mettre à jour l'URL de l'avatar dans la base de données
    avatar_url = f"/{settings.UPLOAD_DIR}/avatars/{unique_filename}"
    crud.user.update(db=db, db_obj=user, obj_in={"avatar_url": avatar_url})

    return schemas.AvatarUploadResponse(
        avatar_url=avatar_url,
        message="Avatar uploadé avec succès"
    )


@router.delete(
    "/{user_id}/avatar",
    status_code=status.HTTP_200_OK,
    summary="Supprimer la photo de profil",
    description="Supprime la photo de profil de l'utilisateur.",
)
def delete_avatar(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a user's profile picture.
    """
    # Vérifier que l'utilisateur existe
    user = crud.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    # Vérifier les permissions
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à supprimer l'avatar de cet utilisateur"
        )

    # Supprimer le fichier si existant
    if user.avatar_url:
        avatar_path = Path(user.avatar_url.lstrip("/"))
        if avatar_path.exists():
            try:
                avatar_path.unlink()
            except OSError:
                pass

        # Mettre à jour la base de données
        crud.user.update(db=db, db_obj=user, obj_in={"avatar_url": None})

    return {"message": "Avatar supprimé avec succès"}
