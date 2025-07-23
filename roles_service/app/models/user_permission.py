from sqlmodel import SQLModel, Field
from typing import Optional
import uuid

class UserPermission(SQLModel, table=True):
    """Permisos específicos asignados a usuarios individuales"""
    uid: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)  # UUID como string sin guiones
    user_id: str = Field(index=True, max_length=100)  # ID del usuario
    permission_name: str = Field(index=True, max_length=100)  # Nombre del permiso
    granted: bool = Field(default=True)  # True = concedido, False = denegado
    granted_by: Optional[str] = None  # ID del admin que otorgó el permiso
    created_at: Optional[str] = None
    
    class Config:
        table_name = "userpermission"  # Nombre correcto de la tabla
