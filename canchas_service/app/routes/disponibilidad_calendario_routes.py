from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from database import get_session
from controllers.disponibilidad_validador import DisponibilidadValidador
from auth.auth_middleware import verify_token
from typing import List
from datetime import date, datetime

router = APIRouter(prefix="/canchas", tags=["Disponibilidad y Calendario"])

@router.get("/{cancha_id}/disponibilidad/{fecha}")
def consultar_disponibilidad_fecha(
    cancha_id: str,
    fecha: date,
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """Consultar disponibilidad completa de una cancha para una fecha específica"""
    validador = DisponibilidadValidador(db)
    
    # Verificar si la cancha tiene configuración
    config_valida, config_msg = validador.validar_configuracion_cancha(cancha_id)
    if not config_valida:
        raise HTTPException(status_code=400, detail=config_msg)
    
    bloques_disponibles = validador.obtener_bloques_disponibles_fecha(cancha_id, fecha)
    bloques_ocupados = validador.obtener_bloques_ocupados_fecha(cancha_id, fecha)
    
    return {
        "cancha_id": cancha_id,
        "fecha": fecha,
        "total_bloques_disponibles": len(bloques_disponibles),
        "total_bloques_ocupados": len(bloques_ocupados),
        "bloques_disponibles": bloques_disponibles,
        "bloques_ocupados": bloques_ocupados
    }

@router.get("/{cancha_id}/bloques-disponibles/{fecha}")
def obtener_bloques_disponibles(
    cancha_id: str,
    fecha: date,
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """Obtener solo los bloques disponibles para reservar en una fecha"""
    validador = DisponibilidadValidador(db)
    
    # Verificar configuración
    config_valida, config_msg = validador.validar_configuracion_cancha(cancha_id)
    if not config_valida:
        raise HTTPException(status_code=400, detail=config_msg)
    
    bloques_disponibles = validador.obtener_bloques_disponibles_fecha(cancha_id, fecha)
    
    return {
        "cancha_id": cancha_id,
        "fecha": fecha,
        "bloques_disponibles": bloques_disponibles,
        "total_disponibles": len(bloques_disponibles)
    }

@router.get("/{cancha_id}/calendario")
def obtener_calendario_mes(
    cancha_id: str,
    year: int = Query(None, description="Año (ej: 2025)"),
    month: int = Query(None, description="Mes (1-12)"),
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """Obtener calendario de disponibilidad para un mes completo"""
    
    # Usar el año y mes actual si no se proporcionan
    from datetime import datetime
    current_date = datetime.now()
    
    if year is None:
        year = current_date.year
    
    if month is None:
        month = current_date.month
    
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="El mes debe estar entre 1 y 12")
    
    validador = DisponibilidadValidador(db)
    
    # Verificar configuración
    config_valida, config_msg = validador.validar_configuracion_cancha(cancha_id)
    
    # En lugar de devolver un error 400, simplemente indicamos que no hay configuración
    # pero igualmente devolvemos la estructura del calendario (vacío)
    from calendar import monthrange
    import datetime as dt
    
    # Obtener días del mes
    _, dias_en_mes = monthrange(year, month)
    calendario = {}
    
    # Si no hay configuración válida, simplemente registrarlo en el resultado
    if not config_valida:
        configuracion_mensaje = config_msg
    
    for dia in range(1, dias_en_mes + 1):
        fecha = date(year, month, dia)
        bloques_disponibles = validador.obtener_bloques_disponibles_fecha(cancha_id, fecha)
        bloques_ocupados = validador.obtener_bloques_ocupados_fecha(cancha_id, fecha)
        
        calendario[str(fecha)] = {
            "dia_semana": fecha.strftime("%A"),
            "total_disponibles": len(bloques_disponibles),
            "total_ocupados": len(bloques_ocupados),
            "bloques_disponibles": bloques_disponibles,
            "bloques_ocupados": bloques_ocupados
        }
    
    return {
        "cancha_id": cancha_id,
        "año": year,
        "mes": month,
        "calendario": calendario,
        "configuracion_valida": config_valida,
        "configuracion_mensaje": config_msg if not config_valida else "Configuración correcta",
        "total_bloques": len(calendario)
    }

@router.post("/{cancha_id}/validar-reserva")
def validar_posible_reserva(
    cancha_id: str,
    fecha_inicio: datetime,
    fecha_fin: datetime,
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """Validar si es posible hacer una reserva sin crearla"""
    validador = DisponibilidadValidador(db)
    
    # Verificar configuración
    config_valida, config_msg = validador.validar_configuracion_cancha(cancha_id)
    if not config_valida:
        return {
            "es_valida": False,
            "mensaje": config_msg,
            "precio": 0.0
        }
    
    # Validar la reserva
    es_valida, mensaje = validador.validar_reserva_bloques(cancha_id, fecha_inicio, fecha_fin)
    
    precio = 0.0
    if es_valida:
        precio = validador.obtener_precio_bloque(cancha_id, fecha_inicio, fecha_fin)
    
    return {
        "es_valida": es_valida,
        "mensaje": mensaje,
        "precio": precio,
        "cancha_id": cancha_id,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin
    }

@router.get("/{cancha_id}/resumen-configuracion")
def obtener_resumen_configuracion(
    cancha_id: str,
    db: Session = Depends(get_session),
    token_data: dict = Depends(verify_token)
):
    """Obtener resumen de la configuración de disponibilidad de una cancha"""
    validador = DisponibilidadValidador(db)
    
    # Verificar configuración básica
    config_valida, config_msg = validador.validar_configuracion_cancha(cancha_id)
    
    # Obtener estadísticas
    from controllers.cancha_disponibilidad_controller import CanchaDisponibilidadController
    from controllers.cancha_dia_especial_controller import CanchaDiaEspecialController
    
    disponibilidad_controller = CanchaDisponibilidadController(db)
    dia_especial_controller = CanchaDiaEspecialController(db)
    
    # Estadísticas de bloques configurados
    todas_disponibilidades = disponibilidad_controller.obtener_disponibilidades_cancha(cancha_id)
    
    estadisticas_bloques = {
        "total_bloques": len(todas_disponibilidades),
        "bloques_disponibles": len([b for b in todas_disponibilidades if b.estado == "disponible"]),
        "bloques_no_disponibles": len([b for b in todas_disponibilidades if b.estado == "no_disponible"]),
        "bloques_mantenimiento": len([b for b in todas_disponibilidades if b.estado == "mantenimiento"]),
    }
    
    # Estadísticas de días especiales
    from datetime import date, timedelta
    hoy = date.today()
    en_un_año = hoy + timedelta(days=365)
    
    dias_especiales = dia_especial_controller.obtener_dias_especiales_cancha(cancha_id, hoy, en_un_año)
    
    estadisticas_dias_especiales = {
        "total_dias_especiales": len(dias_especiales),
        "feriados": len([d for d in dias_especiales if d.tipo == "feriado"]),
        "mantenimientos": len([d for d in dias_especiales if d.tipo == "mantenimiento"]),
        "eventos_especiales": len([d for d in dias_especiales if d.tipo == "evento_especial"]),
    }
    
    return {
        "cancha_id": cancha_id,
        "configuracion_valida": config_valida,
        "mensaje_configuracion": config_msg,
        "estadisticas_bloques": estadisticas_bloques,
        "estadisticas_dias_especiales": estadisticas_dias_especiales,
        "proximos_dias_especiales": dias_especiales[:5]  # Próximos 5 días especiales
    }
