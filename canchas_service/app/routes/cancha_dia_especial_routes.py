from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from database import get_session
from controllers.cancha_dia_especial_controller import CanchaDiaEspecialController
from models.cancha_dia_especial_model import (
    CanchaDiaEspecialCreate, CanchaDiaEspecialUpdate, CanchaDiaEspecialResponse,
    TipoDiaEspecial, EstadoDiaEspecial
)
from typing import List, Optional
from datetime import date

router = APIRouter(prefix="/canchas/dias-especiales", tags=["Días Especiales de Canchas"])

@router.post("/create", response_model=CanchaDiaEspecialResponse)
def crear_dia_especial(
    dia_especial_data: CanchaDiaEspecialCreate,
    db: Session = Depends(get_session)
    # token_data: dict = Depends(verificar_token)  # Comentado temporalmente
):
    """Crear un día especial para una cancha"""
    controller = CanchaDiaEspecialController(db)
    # usuario_id = token_data.get("user_id")  # Comentado temporalmente
    return controller.crear_dia_especial(dia_especial_data)

@router.get("/cancha/{cancha_id}", response_model=List[CanchaDiaEspecialResponse])
def obtener_dias_especiales_cancha(
    cancha_id: str,
    fecha_desde: Optional[date] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    db: Session = Depends(get_session)
    # token_data: dict = Depends(verificar_token)  # Comentado temporalmente
):
    """Obtener días especiales de una cancha, opcionalmente filtrados por rango de fechas"""
    controller = CanchaDiaEspecialController(db)
    return controller.obtener_dias_especiales_cancha(cancha_id, fecha_desde, fecha_hasta)

@router.get("/cancha/{cancha_id}/fecha/{fecha}", response_model=CanchaDiaEspecialResponse)
def obtener_dia_especial_fecha(
    cancha_id: str,
    fecha: date,
    db: Session = Depends(get_session)
    # token_data: dict = Depends(verificar_token)  # Comentado temporalmente
):
    """Obtener día especial para una fecha específica"""
    controller = CanchaDiaEspecialController(db)
    dia_especial = controller.obtener_dia_especial_fecha(cancha_id, fecha)
    if not dia_especial:
        raise HTTPException(status_code=404, detail="No hay día especial configurado para esta fecha")
    return dia_especial

@router.put("/{dia_especial_id}", response_model=CanchaDiaEspecialResponse)
def actualizar_dia_especial(
    dia_especial_id: str,
    update_data: CanchaDiaEspecialUpdate,
    db: Session = Depends(get_session)
    # token_data: dict = Depends(verificar_token)  # Comentado temporalmente
):
    """Actualizar un día especial existente"""
    controller = CanchaDiaEspecialController(db)
    return controller.actualizar_dia_especial(dia_especial_id, update_data)

@router.delete("/{dia_especial_id}")
def eliminar_dia_especial(
    dia_especial_id: str,
    db: Session = Depends(get_session)
    # token_data: dict = Depends(verificar_token)  # Comentado temporalmente
):
    """Eliminar un día especial"""
    controller = CanchaDiaEspecialController(db)
    success = controller.eliminar_dia_especial(dia_especial_id)
    return {"message": "Día especial eliminado exitosamente", "success": success}

# Endpoints especializados
@router.post("/cancha/{cancha_id}/feriados/{year}", response_model=List[CanchaDiaEspecialResponse])
def crear_feriados_anuales(
    cancha_id: str,
    year: int,
    feriados_data: List[CanchaDiaEspecialCreate],
    db: Session = Depends(get_session)
    # token_data: dict = Depends(verificar_token)  # Comentado temporalmente
):
    """Crear feriados para todo un año específico"""
    controller = CanchaDiaEspecialController(db)
    return controller.crear_feriados_anuales(cancha_id, year, feriados_data)

@router.get("/cancha/{cancha_id}/feriados/{year}/{month}", response_model=List[CanchaDiaEspecialResponse])
def obtener_feriados_mes(
    cancha_id: str,
    year: int,
    month: int,
    db: Session = Depends(get_session)
    # token_data: dict = Depends(verificar_token)  # Comentado temporalmente
):
    """Obtener feriados de un mes específico"""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="El mes debe estar entre 1 y 12")
    
    controller = CanchaDiaEspecialController(db)
    return controller.obtener_feriados_mes(cancha_id, year, month)

@router.post("/cancha/{cancha_id}/mantenimiento", response_model=List[CanchaDiaEspecialResponse])
def marcar_mantenimiento(
    cancha_id: str,
    fecha_inicio: date = Query(..., description="Fecha de inicio del mantenimiento"),
    fecha_fin: date = Query(..., description="Fecha de fin del mantenimiento"),
    descripcion: str = Query(..., description="Descripción del mantenimiento"),
    db: Session = Depends(get_session)
    # token_data: dict = Depends(verificar_token)  # Comentado temporalmente
):
    """Marcar período de mantenimiento para una cancha"""
    controller = CanchaDiaEspecialController(db)
    return controller.marcar_mantenimiento(cancha_id, fecha_inicio, fecha_fin, descripcion)

# Endpoints de consulta rápida
@router.get("/cancha/{cancha_id}/tipo/{tipo_dia}", response_model=List[CanchaDiaEspecialResponse])
def obtener_dias_por_tipo(
    cancha_id: str,
    tipo_dia: TipoDiaEspecial,
    year: Optional[int] = Query(None, description="Filtrar por año"),
    db: Session = Depends(get_session)
    # token_data: dict = Depends(verificar_token)  # Comentado temporalmente
):
    """Obtener días especiales por tipo (feriado, evento_especial, mantenimiento, etc.)"""
    controller = CanchaDiaEspecialController(db)
    
    if year:
        fecha_desde = date(year, 1, 1)
        fecha_hasta = date(year, 12, 31)
        dias_especiales = controller.obtener_dias_especiales_cancha(cancha_id, fecha_desde, fecha_hasta)
    else:
        dias_especiales = controller.obtener_dias_especiales_cancha(cancha_id)
    
    # Filtrar por tipo
    dias_filtrados = [dia for dia in dias_especiales if dia.tipo == tipo_dia]
    return dias_filtrados

@router.get("/cancha/{cancha_id}/cerrados/{year}", response_model=List[CanchaDiaEspecialResponse])
def obtener_dias_cerrados_year(
    cancha_id: str,
    year: int,
    db: Session = Depends(get_session)
    # token_data: dict = Depends(verificar_token)  # Comentado temporalmente
):
    """Obtener todos los días que la cancha estará cerrada en un año específico"""
    controller = CanchaDiaEspecialController(db)
    
    fecha_desde = date(year, 1, 1)
    fecha_hasta = date(year, 12, 31)
    dias_especiales = controller.obtener_dias_especiales_cancha(cancha_id, fecha_desde, fecha_hasta)
    
    # Filtrar días cerrados
    dias_cerrados = [
        dia for dia in dias_especiales 
        if dia.estado == EstadoDiaEspecial.CERRADO
    ]
    return dias_cerrados
