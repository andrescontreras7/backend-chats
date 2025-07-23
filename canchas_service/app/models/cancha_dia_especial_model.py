from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, time, date
from enum import Enum
import uuid

class TipoDiaEspecial(str, Enum):
    FERIADO = "feriado"
    EVENTO_ESPECIAL = "evento_especial"
    MANTENIMIENTO = "mantenimiento"
    CIERRE_TEMPORAL = "cierre_temporal"
    HORARIO_EXTENDIDO = "horario_extendido"

class EstadoDiaEspecial(str, Enum):
    CERRADO = "cerrado"
    ABIERTO = "abierto"
    HORARIO_ESPECIAL = "horario_especial"

# Modelo base para días especiales
class CanchaDiaEspecialBase(SQLModel):
    cancha_id: str = Field(foreign_key="canchas.cancha_id", description="ID de la cancha")
    fecha: date = Field(description="Fecha específica (YYYY-MM-DD)")
    tipo: TipoDiaEspecial = Field(description="Tipo de día especial")
    estado: EstadoDiaEspecial = Field(description="Estado de la cancha en esta fecha")
    hora_inicio: Optional[time] = Field(default=None, description="Hora de inicio (solo para horario_especial)")
    hora_fin: Optional[time] = Field(default=None, description="Hora de fin (solo para horario_especial)")
    precio_especial: Optional[float] = Field(default=None, description="Precio especial para esta fecha")
    descripcion: str = Field(max_length=500, description="Descripción del día especial")
    notas: Optional[str] = Field(default=None, max_length=500, description="Notas adicionales")

class CanchaDiaEspecial(CanchaDiaEspecialBase, table=True):
    __tablename__ = "cancha_dias_especiales"
    
    dia_especial_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        primary_key=True,
        max_length=32,
        description="ID único del día especial"
    )
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)
    fecha_actualizacion: Optional[datetime] = Field(default=None)
    creado_por: Optional[str] = Field(default=None, max_length=32, description="ID del usuario admin que lo creó")
    
    # Relación con cancha (opcional para consultas)
    # cancha: Optional["Cancha"] = Relationship(back_populates="dias_especiales")

class CanchaDiaEspecialCreate(CanchaDiaEspecialBase):
    pass

class CanchaDiaEspecialUpdate(SQLModel):
    tipo: Optional[TipoDiaEspecial] = Field(default=None)
    estado: Optional[EstadoDiaEspecial] = Field(default=None)
    hora_inicio: Optional[time] = Field(default=None)
    hora_fin: Optional[time] = Field(default=None)
    precio_especial: Optional[float] = Field(default=None)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    notas: Optional[str] = Field(default=None, max_length=500)

class CanchaDiaEspecialResponse(CanchaDiaEspecialBase):
    dia_especial_id: str
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    creado_por: Optional[str] = None

# Esquemas para consultas específicas
class ConsultaDisponibilidadFecha(SQLModel):
    """Esquema para consultar disponibilidad en una fecha específica"""
    cancha_id: str
    fecha: date

class DisponibilidadDiaCompleto(SQLModel):
    """Respuesta con disponibilidad completa de un día"""
    cancha_id: str
    fecha: date
    es_dia_especial: bool
    dia_especial: Optional[CanchaDiaEspecialResponse] = None
    bloques_disponibles: list = Field(default_factory=list)  # Lista de horarios disponibles
    bloques_ocupados: list = Field(default_factory=list)     # Lista de horarios con reservas

# Esquemas para operaciones bulk de días especiales
class DiaEspecialBulkCreate(SQLModel):
    """Para crear múltiples días especiales de una vez"""
    cancha_id: str
    dias_especiales: list[CanchaDiaEspecialCreate]

class FeriadosAnuales(SQLModel):
    """Para configurar feriados de todo el año"""
    cancha_id: str
    year: int
    feriados: list[CanchaDiaEspecialCreate]
