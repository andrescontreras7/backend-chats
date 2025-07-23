from sqlmodel import SQLModel, Field
from typing import Optional
import uuid

class UserRole(SQLModel, table=True):
    uid: str = Field(default_factory=lambda: str(uuid.uuid4()).replace('-', ''), primary_key=True, max_length=32)
    user_id: str  # ID que viene del auth_service  
    role_id: str  # UUID del rol (string con guiones para compatibilidad)
