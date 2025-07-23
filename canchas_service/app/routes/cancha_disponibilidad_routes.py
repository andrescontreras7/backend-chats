from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from database import get_session
from controllers.cancha_disponibilidad_controller import CanchaDisponibilidadController
from models.cancha_disponibilidad_model import (
    CanchaDisponibilidadCreate, CanchaDisponibilidadUpdate, CanchaDisponibilidadResponse,
    DiasSemana, EstadoDisponibilidad
)
from auth.auth_middleware import verify_token
from typing import List, Optional
from datetime import date

router = APIRouter(prefix="/canchas/disponibilidad", tags=["Disponibilidad de Canchas"])

@router.post("/create", response_model=CanchaDisponibilidadResponse)
def crear_disponibilidad(
    disponibilidad_data: CanchaDisponibilidadCreate,
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """Crear un bloque de disponibilidad específico para una cancha"""
    controller = CanchaDisponibilidadController(db)
    return controller.crear_disponibilidad(disponibilidad_data)

@router.post("/cancha/{cancha_id}/setup-completo", response_model=List[CanchaDisponibilidadResponse])
def setup_horario_completo(
    cancha_id: str,
    tipo_horario: str = Query(default="completo", regex="^(completo|laboral)$"),
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """
    Configurar horario completo para una cancha
    - completo: Lunes a Domingo, 6:00 a 23:00 (17 bloques por día)
    - laboral: Lunes a Viernes, 8:00 a 18:00 (10 bloques por día)
    """
    controller = CanchaDisponibilidadController(db)
    return controller.crear_horario_completo_cancha(cancha_id, tipo_horario)

@router.get("/cancha/{cancha_id}", response_model=List[CanchaDisponibilidadResponse])
def obtener_disponibilidades_cancha(
    cancha_id: str,
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """Obtener todas las disponibilidades configuradas para una cancha"""
    controller = CanchaDisponibilidadController(db)
    return controller.obtener_disponibilidades_cancha(cancha_id)

@router.get("/cancha/{cancha_id}/dia/{dia_semana}", response_model=List[CanchaDisponibilidadResponse])
def obtener_disponibilidades_dia(
    cancha_id: str,
    dia_semana: DiasSemana,
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """Obtener disponibilidades de una cancha para un día específico de la semana"""
    controller = CanchaDisponibilidadController(db)
    return controller.obtener_disponibilidades_dia(cancha_id, dia_semana)

@router.get("/cancha/{cancha_id}/fecha/{fecha}", response_model=List[CanchaDisponibilidadResponse])
def obtener_bloques_disponibles_fecha(
    cancha_id: str,
    fecha: date,
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """Obtener bloques disponibles para una fecha específica"""
    controller = CanchaDisponibilidadController(db)
    return controller.obtener_bloques_disponibles_fecha(cancha_id, fecha)

@router.put("/{disponibilidad_id}", response_model=CanchaDisponibilidadResponse)
def actualizar_disponibilidad(
    disponibilidad_id: str,
    update_data: CanchaDisponibilidadUpdate,
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """Actualizar una disponibilidad existente"""
    controller = CanchaDisponibilidadController(db)
    return controller.actualizar_disponibilidad(disponibilidad_id, update_data)

@router.put("/{disponibilidad_id}/estado", response_model=CanchaDisponibilidadResponse)
def cambiar_estado_bloque(
    disponibilidad_id: str,
    nuevo_estado: EstadoDisponibilidad,
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """Cambiar el estado de un bloque específico (disponible, no_disponible, mantenimiento)"""
    controller = CanchaDisponibilidadController(db)
    return controller.cambiar_estado_bloque(disponibilidad_id, nuevo_estado)

@router.delete("/{disponibilidad_id}")
def eliminar_disponibilidad(
    disponibilidad_id: str,
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """Eliminar una disponibilidad"""
    controller = CanchaDisponibilidadController(db)
    success = controller.eliminar_disponibilidad(disponibilidad_id)
    return {"message": "Disponibilidad eliminada exitosamente", "success": success}

# Endpoints administrativos adicionales
@router.post("/cancha/{cancha_id}/bloque-masivo", response_model=List[CanchaDisponibilidadResponse])
def crear_bloques_masivos(
    cancha_id: str,
    bloques_data: List[CanchaDisponibilidadCreate],
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """Crear múltiples bloques de disponibilidad de una vez"""
    controller = CanchaDisponibilidadController(db)
    resultados = []
    
    for bloque_data in bloques_data:
        bloque_data.cancha_id = cancha_id  # Asegurar que use el cancha_id del path
        resultado = controller.crear_disponibilidad(bloque_data)
        resultados.append(resultado)
    
    return resultados

@router.put("/cancha/{cancha_id}/dia/{dia_semana}/estado", response_model=List[CanchaDisponibilidadResponse])
def cambiar_estado_dia_completo(
    cancha_id: str,
    dia_semana: DiasSemana,
    nuevo_estado: EstadoDisponibilidad,
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """Cambiar el estado de todos los bloques de un día específico"""
    controller = CanchaDisponibilidadController(db)
    
    # Obtener todas las disponibilidades del día
    disponibilidades = controller.obtener_disponibilidades_dia(cancha_id, dia_semana)
    
    resultados = []
    for disp in disponibilidades:
        resultado = controller.cambiar_estado_bloque(disp.disponibilidad_id, nuevo_estado)
        resultados.append(resultado)
    
    return resultados

@router.delete("/cancha/{cancha_id}/reset")
def reset_disponibilidades_cancha(
    cancha_id: str,
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """Eliminar todas las disponibilidades de una cancha (para reconfigurar)"""
    controller = CanchaDisponibilidadController(db)
    
    # Obtener todas las disponibilidades
    disponibilidades = controller.obtener_disponibilidades_cancha(cancha_id)
    
    # Eliminar una por una
    eliminadas = 0
    for disp in disponibilidades:
        controller.eliminar_disponibilidad(disp.disponibilidad_id)
        eliminadas += 1
    
    return {
        "message": f"Se eliminaron {eliminadas} bloques de disponibilidad",
        "cancha_id": cancha_id,
        "total_eliminados": eliminadas
    }
