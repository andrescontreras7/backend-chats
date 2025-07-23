from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
import uuid

class ReservaBase(SQLModel):
    cancha_id: str = Field(max_length=32, description="ID de la cancha reservada")
    fecha_inicio: datetime = Field(description="Fecha y hora de inicio de la reserva")
    fecha_fin: datetime = Field(description="Fecha y hora de fin de la reserva")
    estado: str = Field(default="pendiente", max_length=50, description="Estado de la reserva (pendiente, confirmada, cancelada)")
    notas: Optional[str] = Field(default=None, max_length=500, description="Notas adicionales de la reserva")

class ReservaCreate(SQLModel):
    cancha_id: str = Field(max_length=32, description="ID de la cancha reservada")
    fecha_inicio: datetime = Field(description="Fecha y hora de inicio de la reserva")
    fecha_fin: datetime = Field(description="Fecha y hora de fin de la reserva")
    notas: Optional[str] = Field(default=None, max_length=500, description="Notas adicionales de la reserva")

class ReservaFull(SQLModel):
    cancha_id: str = Field(max_length=32, description="ID de la cancha reservada")
    user_id: str = Field(max_length=32, description="ID del usuario que hace la reserva")
    
    # Snapshot de datos del usuario al momento de la reserva
    user_email: Optional[str] = Field(default=None, max_length=255, description="Email del usuario al momento de la reserva")
    user_nombre: Optional[str] = Field(default=None, max_length=255, description="Nombre del usuario al momento de la reserva")
    user_telefono: Optional[str] = Field(default=None, max_length=20, description="Teléfono del usuario al momento de la reserva")
    
    fecha_inicio: datetime = Field(description="Fecha y hora de inicio de la reserva")
    fecha_fin: datetime = Field(description="Fecha y hora de fin de la reserva")
    precio_total: float = Field(description="Precio total de la reserva")
    estado: str = Field(default="pendiente", max_length=50, description="Estado de la reserva (pendiente, confirmada, cancelada)")
    notas: Optional[str] = Field(default=None, max_length=500, description="Notas adicionales de la reserva")

class Reserva(ReservaFull, table=True):
    __tablename__ = "reservas"
    
    reserva_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        primary_key=True,
        max_length=32,
        description="ID único de la reserva"
    )
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    fecha_actualizacion: Optional[datetime] = Field(default=None)

class ReservaUpdate(SQLModel):
    fecha_inicio: Optional[datetime] = Field(default=None)
    fecha_fin: Optional[datetime] = Field(default=None)
    precio_total: Optional[float] = Field(default=None)
    estado: Optional[str] = Field(default=None, max_length=50)
    notas: Optional[str] = Field(default=None, max_length=500)

class ReservaResponse(ReservaBase):
    reserva_id: str
    user_id: str = Field(description="ID del usuario que hizo la reserva")
    precio_total: float = Field(description="Precio total de la reserva")
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None

class UsuarioInfo(SQLModel):
    """Información básica del usuario para mostrar en reservas"""
    user_id: str
    username: str
    email: str
    nombre_completo: Optional[str] = None

class ReservaConUsuario(ReservaResponse):
    """Respuesta de reserva con información completa del usuario"""
    usuario: Optional[UsuarioInfo] = Field(default=None, description="Información del usuario que hizo la reserva")
