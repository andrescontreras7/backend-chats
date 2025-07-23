from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid

class CanchaBase(SQLModel):
    nombre: str = Field(max_length=255, description="Nombre de la cancha")
    descripcion: Optional[str] = Field(default=None, max_length=500, description="Descripción de la cancha")
    tipo_deporte: str = Field(max_length=100, description="Tipo de deporte (fútbol, básquet, tenis, etc.)")
    capacidad_jugadores: int = Field(description="Número máximo de jugadores")
    precio_por_hora: float = Field(description="Precio por hora de uso")
    disponible: bool = Field(default=True, description="Si la cancha está disponible")
    ubicacion: Optional[str] = Field(default=None, max_length=500, description="Ubicación o dirección")
    imagen_url: Optional[str] = Field(default=None, max_length=500, description="URL de la imagen de la cancha")

class Cancha(CanchaBase, table=True):
    __tablename__ = "canchas"
    
    cancha_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        primary_key=True,
        max_length=32,
        description="ID único de la cancha"
    )
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    fecha_actualizacion: Optional[datetime] = Field(default=None)

class CanchaCreate(CanchaBase):
    pass

class CanchaUpdate(SQLModel):
    nombre: Optional[str] = Field(default=None, max_length=255)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    tipo_deporte: Optional[str] = Field(default=None, max_length=100)
    capacidad_jugadores: Optional[int] = Field(default=None)
    precio_por_hora: Optional[float] = Field(default=None)
    disponible: Optional[bool] = Field(default=None)
    ubicacion: Optional[str] = Field(default=None, max_length=500)
    imagen_url: Optional[str] = Field(default=None, max_length=500)

class CanchaResponse(CanchaBase):
    cancha_id: str
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
