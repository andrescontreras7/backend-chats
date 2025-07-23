from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class ReservaSchema(BaseModel):
    reserva_id: str
    cancha_id: str
    user_id: str
    fecha_inicio: datetime
    fecha_fin: datetime
    precio_total: float
    estado: str
    notas: Optional[str] = None
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReservaCreateSchema(BaseModel):
    cancha_id: str = Field(..., min_length=1)
    fecha_inicio: datetime
    fecha_fin: datetime
    notas: Optional[str] = Field(None, max_length=500)

    @validator('fecha_fin')
    def fecha_fin_debe_ser_posterior(cls, v, values, **kwargs):
        if 'fecha_inicio' in values and v <= values['fecha_inicio']:
            raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return v

    @validator('fecha_inicio')
    def fecha_inicio_debe_ser_futura(cls, v):
        # Convertir ambas fechas a naive para comparar
        now = datetime.utcnow()
        if hasattr(v, 'tzinfo') and v.tzinfo is not None:
            v_naive = v.replace(tzinfo=None)
        else:
            v_naive = v
        
        # Permitir reservas en el mismo día (siempre que la hora sea igual o posterior)
        # Esto implica que si ahora son las 15:30, se podrían hacer reservas desde las 15:30 en adelante
        if v_naive.date() < now.date():
            raise ValueError('La fecha de inicio debe ser para hoy o en el futuro')
        elif v_naive.date() == now.date() and v_naive.time() < now.time():
            raise ValueError('La hora de inicio debe ser igual o posterior a la hora actual')
        return v

class ReservaUpdateSchema(BaseModel):
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    estado: Optional[str] = Field(None, pattern="^(pendiente|confirmada|cancelada)$")
    notas: Optional[str] = Field(None, max_length=500)

    @validator('fecha_fin')
    def fecha_fin_debe_ser_posterior(cls, v, values, **kwargs):
        if v and 'fecha_inicio' in values and values['fecha_inicio'] and v <= values['fecha_inicio']:
            raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return v
