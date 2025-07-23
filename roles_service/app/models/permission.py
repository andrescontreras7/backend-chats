from sqlmodel import SQLModel, Field
from typing import Optional
import uuid

class Permission(SQLModel, table=True):
    uid: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, unique=True, max_length=100)
    description: Optional[str] = None
