from sqlmodel import SQLModel, Field
from typing import Optional
import uuid

class User(SQLModel, table=True):
    uid:  uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(index=True)
    email: str = Field(index=True, unique=True)
    is_active: bool = Field(default=True)
    last_name: str
    password: str  # Contraseña hasheada
