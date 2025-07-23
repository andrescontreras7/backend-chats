from pydantic import BaseModel, Field
from typing import Optional
import uuid

class RoleCreate(BaseModel):
    name: str = Field(min_length=3, max_length=30)
    description: Optional[str]

class RoleResponse(RoleCreate):
    uid: uuid.UUID

    class Config:
        orm_mode = True

class AssignRoleByName(BaseModel):
    user_id: str = Field(description="UID del usuario al que se asignará el rol")
    role_name: str = Field(description="Nombre del rol a asignar")

class AssignRoleByUID(BaseModel):
    user_id: str = Field(description="UID del usuario al que se asignará el rol")
    role_uid: str = Field(description="UID del rol a asignar")

class RoleAssignmentResponse(BaseModel):
    message: str
    role_name: str
    role_uid: str
    user_id: str
