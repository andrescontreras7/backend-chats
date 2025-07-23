from pydantic import BaseModel, Field
from typing import Optional
import uuid

class PermissionCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: Optional[str]

class PermissionResponse(PermissionCreate):
    uid: uuid.UUID

    class Config:
        orm_mode = True
