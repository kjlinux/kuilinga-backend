from typing import Generator, Optional, List, Set
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import SessionLocal
from app.schemas.token import TokenPayload
from app.crud.user import user as crud_user
from app.models.user import User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = crud_user.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400, detail="Inactive user")
    return current_user

def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


class PermissionChecker:
    """
    Dependency that checks if the user has the required permissions.
    """

    def __init__(self, required_permissions: List[str]):
        self.required_permissions = set(required_permissions)

    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        user_permissions: Set[str] = set()
        for role in user.roles:
            for permission in role.permissions:
                user_permissions.add(permission.name)

        if user.is_superuser:
            return user

        if not self.required_permissions.issubset(user_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissions insuffisantes pour effectuer cette action.",
            )
        return user


def require_role(required_role: str):
    """
    Dependency that checks if the user has the required role.
    """

    def role_checker(user: User = Depends(get_current_active_user)) -> User:
        user_roles = {role.name for role in user.roles}

        if user.is_superuser or required_role in user_roles:
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Le rôle '{required_role}' est requis pour effectuer cette action.",
            )

    return role_checker


from app.models.employee import Employee

def get_current_active_employee(
    current_user: User = Depends(get_current_active_user),
) -> Employee:
    if not current_user.employee:
        raise HTTPException(
            status_code=403, detail="Access forbidden: User is not an employee."
        )
    return current_user.employee


def get_current_active_manager(
    current_user: User = Depends(get_current_active_user),
) -> Employee:
    """
    Checks if the user has the 'manager' role and is an employee.
    Returns the Employee object with department information.
    """
    user_roles = {role.name for role in current_user.roles}
    if "manager" not in user_roles and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Access forbidden: Manager role required.",
        )

    if not current_user.employee or not current_user.employee.department_id:
        raise HTTPException(
            status_code=403,
            detail="Access forbidden: Manager is not associated with a department.",
        )

    return current_user.employee
