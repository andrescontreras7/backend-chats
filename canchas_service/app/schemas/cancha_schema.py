from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CanchaSchema(BaseModel):
    cancha_id: str
    nombre: str
    descripcion: Optional[str] = None
    tipo_deporte: str
    capacidad_jugadores: int
    precio_por_hora: float
    disponible: bool
    ubicacion: Optional[str] = None
    imagen_url: Optional[str] = None
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True

class CanchaCreateSchema(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    descripcion: Optional[str] = Field(None, max_length=500)
    tipo_deporte: str = Field(..., min_length=1, max_length=100)
    capacidad_jugadores: int = Field(..., gt=0)
    precio_por_hora: float = Field(..., gt=0)
    disponible: bool = True
    ubicacion: Optional[str] = Field(None, max_length=500)
    imagen_url: Optional[str] = Field(None, max_length=500)

class CanchaUpdateSchema(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = Field(None, max_length=500)
    tipo_deporte: Optional[str] = Field(None, min_length=1, max_length=100)
    capacidad_jugadores: Optional[int] = Field(None, gt=0)
    precio_por_hora: Optional[float] = Field(None, gt=0)
    disponible: Optional[bool] = None
    ubicacion: Optional[str] = Field(None, max_length=500)
    imagen_url: Optional[str] = Field(None, max_length=500)
