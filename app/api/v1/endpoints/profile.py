from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
import shutil
import os
from app import crud, models, schemas
from app.dependencies import get_db, get_current_active_user

router = APIRouter()

@router.get(
    "/me",
    response_model=schemas.User,
    summary="Lire les informations de son propre profil",
)
def read_current_user(
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user profile.
    """
    return current_user

@router.put(
    "/me",
    response_model=schemas.User,
    summary="Mettre à jour son propre profil",
)
def update_current_user_profile(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserUpdateProfile,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Update current user profile.
    """
    user = crud.user.update(db=db, db_obj=current_user, obj_in=user_in)
    return user

@router.put(
    "/me/password",
    response_model=schemas.User,
    summary="Changer son propre mot de passe",
)
def update_current_user_password(
    *,
    db: Session = Depends(get_db),
    password_in: schemas.UserUpdatePassword,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Update current user password.
    """
    from app.core.security import verify_password
    if not verify_password(password_in.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le mot de passe actuel est incorrect")

    user_update = schemas.UserUpdate(password=password_in.new_password)
    user = crud.user.update(db=db, db_obj=current_user, obj_in=user_update)
    return user

@router.post(
    "/me/upload-picture",
    response_model=schemas.User,
    summary="Télécharger sa photo de profil",
)
def upload_profile_picture(
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Upload profile picture.
    """
    upload_dir = "static/profile_pictures"
    os.makedirs(upload_dir, exist_ok=True)
    file_extension = file.filename.split(".")[-1]
    file_path = f"{upload_dir}/{current_user.id}.{file_extension}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    user_update = schemas.UserUpdate(profile_picture_url=f"/{file_path}")
    user = crud.user.update(db=db, db_obj=current_user, obj_in=user_update)
    return user
