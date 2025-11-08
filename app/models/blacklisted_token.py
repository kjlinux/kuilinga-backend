from sqlalchemy import Column, String, DateTime
from datetime import datetime, timezone
from .base import BaseModel


class BlacklistedToken(BaseModel):
    """
    Model pour stocker les tokens JWT invalidés (blacklist).
    Les tokens sont ajoutés ici lors du logout pour empêcher leur réutilisation.
    """
    __tablename__ = "blacklisted_tokens"

    token = Column(String, unique=True, index=True, nullable=False)
    blacklisted_on = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    user_id = Column(String, nullable=True)  # Optional: pour tracer quel utilisateur a déconnecté

    def __repr__(self):
        return f"<BlacklistedToken {self.token[:20]}... blacklisted at {self.blacklisted_on}>"
