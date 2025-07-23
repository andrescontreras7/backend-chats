from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, time
from enum import Enum
import uuid

class DiasSemana(str, Enum):
    LUNES = "lunes"
    MARTES = "martes"
    MIERCOLES = "miercoles"
    JUEVES = "jueves"
    VIERNES = "viernes"
    SABADO = "sabado"
    DOMINGO = "domingo"

class EstadoDisponibilidad(str, Enum):
    DISPONIBLE = "disponible"
    NO_DISPONIBLE = "no_disponible"
    MANTENIMIENTO = "mantenimiento"

# Modelo base para la disponibilidad de canchas
class CanchaDisponibilidadBase(SQLModel):
    cancha_id: str = Field(foreign_key="canchas.cancha_id", description="ID de la cancha")
    dia_semana: DiasSemana = Field(description="Día de la semana")
    hora_inicio: time = Field(description="Hora de inicio del bloque (formato HH:MM)")
    hora_fin: time = Field(description="Hora de fin del bloque (formato HH:MM)")
    estado: EstadoDisponibilidad = Field(default=EstadoDisponibilidad.DISPONIBLE, description="Estado del bloque")
    precio_especial: Optional[float] = Field(default=None, description="Precio especial para este bloque (opcional)")
    notas: Optional[str] = Field(default=None, max_length=500, description="Notas adicionales")

class CanchaDisponibilidad(CanchaDisponibilidadBase, table=True):
    __tablename__ = "cancha_disponibilidad"
    
    disponibilidad_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        primary_key=True,
        max_length=32,
        description="ID único de la disponibilidad"
    )
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    fecha_actualizacion: Optional[datetime] = Field(default=None)
    
    # Relación con cancha (opcional para consultas)
    # cancha: Optional["Cancha"] = Relationship(back_populates="disponibilidades")

class CanchaDisponibilidadCreate(CanchaDisponibilidadBase):
    pass

class CanchaDisponibilidadUpdate(SQLModel):
    dia_semana: Optional[DiasSemana] = Field(default=None)
    hora_inicio: Optional[time] = Field(default=None)
    hora_fin: Optional[time] = Field(default=None)
    estado: Optional[EstadoDisponibilidad] = Field(default=None)
    precio_especial: Optional[float] = Field(default=None)
    notas: Optional[str] = Field(default=None, max_length=500)

class CanchaDisponibilidadResponse(CanchaDisponibilidadBase):
    disponibilidad_id: str
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None

# Esquemas para operaciones bulk
class CanchaDisponibilidadBulkCreate(SQLModel):
    cancha_id: str
    disponibilidades: List[CanchaDisponibilidadCreate]

class CanchaHorarioCompleto(SQLModel):
    """Esquema para configurar horario completo de una cancha"""
    cancha_id: str
    horario_lunes: List[CanchaDisponibilidadCreate]
    horario_martes: List[CanchaDisponibilidadCreate]
    horario_miercoles: List[CanchaDisponibilidadCreate]
    horario_jueves: List[CanchaDisponibilidadCreate]
    horario_viernes: List[CanchaDisponibilidadCreate]
    horario_sabado: List[CanchaDisponibilidadCreate]
    horario_domingo: List[CanchaDisponibilidadCreate]
