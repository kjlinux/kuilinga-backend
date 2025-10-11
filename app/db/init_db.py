from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
from app.models.user import User
from app.schemas.user import UserCreate
from app.crud.user import create_user

def init_db(db: Session) -> None:
    Base.metadata.create_all(bind=engine)

    user = db.query(User).filter(User.email == settings.FIRST_SUPERUSER).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = create_user(db, user_in)
