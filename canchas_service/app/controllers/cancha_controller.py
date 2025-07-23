from sqlmodel import Session, select
from models.cancha_model import Cancha, CanchaCreate, CanchaUpdate
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime

def create_cancha(cancha_data: CanchaCreate, session: Session) -> Cancha:
    """Crear una nueva cancha"""
    cancha = Cancha(**cancha_data.model_dump())
    session.add(cancha)
    session.commit()
    session.refresh(cancha)
    return cancha

def get_all_canchas(session: Session, skip: int = 0, limit: int = 100, incluir_no_disponibles: bool = False) -> List[Cancha]:
    """Obtener todas las canchas con paginación. Por defecto solo muestra canchas disponibles."""
    if incluir_no_disponibles:
        # Solo para administradores - mostrar todas las canchas
        statement = select(Cancha).offset(skip).limit(limit)
    else:
        # Para usuarios normales - solo canchas disponibles
        statement = select(Cancha).where(Cancha.disponible == True).offset(skip).limit(limit)
    
    canchas = session.exec(statement).all()
    return canchas

def get_cancha_by_id(cancha_id: str, session: Session) -> Cancha:
    """Obtener una cancha por ID"""
    cancha = session.get(Cancha, cancha_id)
    if not cancha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cancha no encontrada"
        )
    return cancha

def update_cancha(cancha_id: str, cancha_data: CanchaUpdate, session: Session) -> Cancha:
    """Actualizar una cancha"""
    cancha = session.get(Cancha, cancha_id)
    if not cancha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cancha no encontrada"
        )
    
    cancha_dict = cancha_data.model_dump(exclude_unset=True)
    for key, value in cancha_dict.items():
        setattr(cancha, key, value)
    
    cancha.fecha_actualizacion = datetime.utcnow()
    session.add(cancha)
    session.commit()
    session.refresh(cancha)
    return cancha

def delete_cancha(cancha_id: str, session: Session) -> dict:
    """Eliminar una cancha"""
    cancha = session.get(Cancha, cancha_id)
    if not cancha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cancha no encontrada"
        )
    
    session.delete(cancha)
    session.commit()
    return {"message": "Cancha eliminada exitosamente"}

def get_canchas_by_tipo(tipo_deporte: str, session: Session, incluir_no_disponibles: bool = False) -> List[Cancha]:
    """Obtener canchas por tipo de deporte. Por defecto solo muestra canchas disponibles."""
    if incluir_no_disponibles:
        # Solo para administradores - mostrar todas las canchas del tipo
        statement = select(Cancha).where(Cancha.tipo_deporte == tipo_deporte)
    else:
        # Para usuarios normales - solo canchas disponibles del tipo
        statement = select(Cancha).where(
            Cancha.tipo_deporte == tipo_deporte,
            Cancha.disponible == True
        )
    
    canchas = session.exec(statement).all()
    return canchas

def get_canchas_disponibles(session: Session) -> List[Cancha]:
    """Obtener solo las canchas disponibles"""
    statement = select(Cancha).where(Cancha.disponible == True)
    canchas = session.exec(statement).all()
    return canchas
