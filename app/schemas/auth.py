from pydantic import BaseModel, Field

class SetInitialPassword(BaseModel):
    token: str = Field(..., example="your_password_reset_token")
    new_password: str = Field(..., min_length=8, example="new_strong_password")
