from sqlmodel import Session, select
from models.reserva_model import Reserva
from models.cancha_disponibilidad_model import CanchaDisponibilidad, DiasSemana, EstadoDisponibilidad
from models.cancha_dia_especial_model import CanchaDiaEspecial, EstadoDiaEspecial
from utils.horario_utils import HorarioUtils
from controllers.cancha_disponibilidad_controller import CanchaDisponibilidadController
from controllers.cancha_dia_especial_controller import CanchaDiaEspecialController
from datetime import datetime, date, time
from typing import Tuple, Optional, List
from fastapi import HTTPException

class DisponibilidadValidador:
    """Validador que integra el sistema de bloques fijos con las reservas"""
    
    def __init__(self, db: Session):
        self.db = db
        self.disponibilidad_controller = CanchaDisponibilidadController(db)
        self.dia_especial_controller = CanchaDiaEspecialController(db)
    
    def validar_reserva_bloques(self, cancha_id: str, fecha_inicio: datetime, fecha_fin: datetime) -> Tuple[bool, str]:
        # Agregar logs para depuración
        print(f"🔍 Validando reserva - Cancha: {cancha_id}")
        print(f"🔍 Fecha inicio: {fecha_inicio} - Fecha fin: {fecha_fin}")
        
     
        es_valido = HorarioUtils.es_horario_valido_reserva(fecha_inicio, fecha_fin)
        print(f"🔍 ¿Horario válido?: {es_valido}")
        
        if not es_valido:
            return False, "La reserva debe ser de exactamente 1 hora y en horarios válidos (06:00-07:00, 07:00-08:00, etc.)"
        
        # 2. Extraer información del bloque
        fecha, hora_inicio, hora_fin = HorarioUtils.convertir_datetime_a_bloque(fecha_inicio, fecha_fin)
        dia_semana = HorarioUtils.date_to_dia_semana(fecha)
        print(f"🔍 Fecha: {fecha}, Día: {dia_semana.value}, Horario: {hora_inicio}-{hora_fin}")
        
        # 3. Verificar si hay día especial para esta fecha
        dia_especial = self.dia_especial_controller.obtener_dia_especial_fecha(cancha_id, fecha)
        
        if dia_especial:
    
            if dia_especial.estado == EstadoDiaEspecial.CERRADO:
                return False, f"La cancha está cerrada el {fecha} ({dia_especial.descripcion})"
            
            elif dia_especial.estado == EstadoDiaEspecial.HORARIO_ESPECIAL:
                # Verificar si el horario solicitado está dentro del horario especial
                if not (dia_especial.hora_inicio <= hora_inicio and hora_fin <= dia_especial.hora_fin):
                    return False, f"El horario solicitado está fuera del horario especial ({dia_especial.hora_inicio}-{dia_especial.hora_fin})"
     
        stmt = select(CanchaDisponibilidad).where(
            CanchaDisponibilidad.cancha_id == cancha_id,
            CanchaDisponibilidad.dia_semana == dia_semana,
            CanchaDisponibilidad.hora_inicio == hora_inicio,
            CanchaDisponibilidad.hora_fin == hora_fin
        )
        bloque_config = self.db.exec(stmt).first()
        
        print(f"🔍 ¿Se encontró configuración para este bloque?: {bloque_config is not None}")
        
        if not bloque_config:
            return False, f"No hay horario configurado para {dia_semana.value} de {hora_inicio} a {hora_fin}"
        
        print(f"🔍 Estado del bloque: {bloque_config.estado.value}")
        
        if bloque_config.estado != EstadoDisponibilidad.DISPONIBLE:
            return False, f"El bloque {hora_inicio}-{hora_fin} no está disponible ({bloque_config.estado.value})"
        
        # 5. Verificar conflictos con reservas existentes
        if self._verificar_conflicto_reservas(cancha_id, fecha_inicio, fecha_fin):
            return False, "Ya existe una reserva en ese horario"
        
        return True, "Reserva válida"
    
    def obtener_precio_bloque(self, cancha_id: str, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        """Obtiene el precio para un bloque específico considerando precios especiales"""
        
        fecha, hora_inicio, hora_fin = HorarioUtils.convertir_datetime_a_bloque(fecha_inicio, fecha_fin)
        dia_semana = HorarioUtils.date_to_dia_semana(fecha)
        
        # Verificar precio especial por día especial
        dia_especial = self.dia_especial_controller.obtener_dia_especial_fecha(cancha_id, fecha)
        if dia_especial and dia_especial.precio_especial:
            return dia_especial.precio_especial
        
        # Verificar precio especial por bloque configurado
        stmt = select(CanchaDisponibilidad).where(
            CanchaDisponibilidad.cancha_id == cancha_id,
            CanchaDisponibilidad.dia_semana == dia_semana,
            CanchaDisponibilidad.hora_inicio == hora_inicio,
            CanchaDisponibilidad.hora_fin == hora_fin
        )
        bloque_config = self.db.exec(stmt).first()
        
        if bloque_config and bloque_config.precio_especial:
            return bloque_config.precio_especial
        
        # Precio por defecto de la cancha
        from models.cancha_model import Cancha
        cancha = self.db.get(Cancha, cancha_id)
        return cancha.precio_por_hora if cancha else 0.0
    
    def obtener_bloques_disponibles_fecha(self, cancha_id: str, fecha: date) -> List[dict]:
        """Obtiene todos los bloques disponibles para una fecha específica"""
        
        dia_semana = HorarioUtils.date_to_dia_semana(fecha)
        bloques_disponibles = []
        
        # Verificar si hay día especial
        dia_especial = self.dia_especial_controller.obtener_dia_especial_fecha(cancha_id, fecha)
        
        if dia_especial and dia_especial.estado == EstadoDiaEspecial.CERRADO:
            return []  # No hay bloques disponibles
        
        # Obtener bloques configurados para este día de semana
        stmt = select(CanchaDisponibilidad).where(
            CanchaDisponibilidad.cancha_id == cancha_id,
            CanchaDisponibilidad.dia_semana == dia_semana,
            CanchaDisponibilidad.estado == EstadoDisponibilidad.DISPONIBLE
        ).order_by(CanchaDisponibilidad.hora_inicio)
        
        bloques_config = self.db.exec(stmt).all()
        
        for bloque in bloques_config:
            # Crear datetime para esta fecha específica
            fecha_inicio = datetime.combine(fecha, bloque.hora_inicio)
            fecha_fin = datetime.combine(fecha, bloque.hora_fin)
            
            # Verificar si hay día especial con horario especial
            if dia_especial and dia_especial.estado == EstadoDiaEspecial.HORARIO_ESPECIAL:
                if not (dia_especial.hora_inicio <= bloque.hora_inicio and bloque.hora_fin <= dia_especial.hora_fin):
                    continue  # Este bloque está fuera del horario especial
            
            # Verificar si no hay conflicto con reservas existentes
            if not self._verificar_conflicto_reservas(cancha_id, fecha_inicio, fecha_fin):
                precio = self.obtener_precio_bloque(cancha_id, fecha_inicio, fecha_fin)
                
                bloques_disponibles.append({
                    "hora_inicio": bloque.hora_inicio,
                    "hora_fin": bloque.hora_fin,
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "precio": precio,
                    "notas": bloque.notas
                })
        
        return bloques_disponibles
    
    def obtener_bloques_ocupados_fecha(self, cancha_id: str, fecha: date) -> List[dict]:
        """Obtiene todos los bloques ocupados (con reservas) para una fecha específica"""
        
        # Buscar reservas para esta fecha
        fecha_inicio_dia = datetime.combine(fecha, time.min)
        fecha_fin_dia = datetime.combine(fecha, time.max)
        
        stmt = select(Reserva).where(
            Reserva.cancha_id == cancha_id,
            Reserva.estado != "cancelada",
            Reserva.fecha_inicio >= fecha_inicio_dia,
            Reserva.fecha_inicio < fecha_fin_dia
        ).order_by(Reserva.fecha_inicio)
        
        reservas = self.db.exec(stmt).all()
        
        bloques_ocupados = []
        for reserva in reservas:
            fecha_res, hora_inicio, hora_fin = HorarioUtils.convertir_datetime_a_bloque(
                reserva.fecha_inicio, reserva.fecha_fin
            )
            
            bloques_ocupados.append({
                "hora_inicio": hora_inicio,
                "hora_fin": hora_fin,
                "fecha_inicio": reserva.fecha_inicio,
                "fecha_fin": reserva.fecha_fin,
                "reserva_id": reserva.reserva_id,
                "user_nombre": reserva.user_nombre,
                "estado": reserva.estado
            })
        
        return bloques_ocupados
    
    def _verificar_conflicto_reservas(self, cancha_id: str, fecha_inicio: datetime, fecha_fin: datetime) -> bool:
        """Verificar conflictos con reservas existentes (método privado)"""
        stmt = select(Reserva).where(
            Reserva.cancha_id == cancha_id,
            Reserva.estado != "cancelada",
            Reserva.fecha_inicio < fecha_fin,
            Reserva.fecha_fin > fecha_inicio
        )
        reservas_conflicto = self.db.exec(stmt).all()
        return len(reservas_conflicto) > 0
    
    def validar_configuracion_cancha(self, cancha_id: str) -> Tuple[bool, str]:
        """Valida si una cancha tiene configuración de disponibilidad"""
        
        # Verificar si tiene al menos algunos bloques configurados
        stmt = select(CanchaDisponibilidad).where(CanchaDisponibilidad.cancha_id == cancha_id)
        bloques = self.db.exec(stmt).all()
        
        if not bloques:
            return False, "La cancha no tiene horarios configurados. Use el endpoint setup-completo primero."
        
        return True, f"Cancha configurada con {len(bloques)} bloques horarios"
