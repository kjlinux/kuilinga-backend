import uuid
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import declared_attr

def generate_uuid():
    return str(uuid.uuid4())

@as_declarative()
class BaseModel:
    id = Column(String, primary_key=True, default=generate_uuid)
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"
