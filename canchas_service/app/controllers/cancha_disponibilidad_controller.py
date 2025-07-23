from sqlmodel import Session, select
from models.cancha_disponibilidad_model import (
    CanchaDisponibilidad, CanchaDisponibilidadCreate, CanchaDisponibilidadUpdate,
    CanchaDisponibilidadResponse, DiasSemana, EstadoDisponibilidad
)
from models.cancha_model import Cancha
from utils.horario_utils import HorarioUtils
from datetime import datetime, date
from typing import List, Optional
from fastapi import HTTPException

class CanchaDisponibilidadController:
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear_disponibilidad(self, disponibilidad_data: CanchaDisponibilidadCreate) -> CanchaDisponibilidadResponse:
        """Crear un bloque de disponibilidad específico"""
        
        # Verificar que la cancha existe
        cancha = self.db.get(Cancha, disponibilidad_data.cancha_id)
        if not cancha:
            raise HTTPException(status_code=404, detail="Cancha no encontrada")
        
        # Validar que el bloque horario sea válido (1 hora exacta)
        if not HorarioUtils.validar_bloque_horario(disponibilidad_data.hora_inicio, disponibilidad_data.hora_fin):
            raise HTTPException(status_code=400, detail="El bloque debe ser de exactamente 1 hora")
        
        # Verificar que no haya conflicto con bloques existentes
        conflicto = self._verificar_conflicto_disponibilidad(
            disponibilidad_data.cancha_id,
            disponibilidad_data.dia_semana,
            disponibilidad_data.hora_inicio,
            disponibilidad_data.hora_fin
        )
        if conflicto:
            raise HTTPException(status_code=400, detail="Ya existe un bloque en este horario")
        
        # Crear la disponibilidad
        nueva_disponibilidad = CanchaDisponibilidad(**disponibilidad_data.model_dump())
        self.db.add(nueva_disponibilidad)
        self.db.commit()
        self.db.refresh(nueva_disponibilidad)
        
        return CanchaDisponibilidadResponse(**nueva_disponibilidad.model_dump())
    
    def crear_horario_completo_cancha(self, cancha_id: str, tipo_horario: str = "completo") -> List[CanchaDisponibilidadResponse]:
        """Crear horario completo para una cancha (todos los días y horas estándar)"""
        
        # Verificar que la cancha existe
        cancha = self.db.get(Cancha, cancha_id)
        if not cancha:
            raise HTTPException(status_code=404, detail="Cancha no encontrada")
        
        # Eliminar horarios existentes para esta cancha
        stmt = select(CanchaDisponibilidad).where(CanchaDisponibilidad.cancha_id == cancha_id)
        disponibilidades_existentes = self.db.exec(stmt).all()
        for disp in disponibilidades_existentes:
            self.db.delete(disp)
        
        # Generar horarios según el tipo
        if tipo_horario == "completo":
            horarios_data = HorarioUtils.generar_horarios_semana_completa(cancha_id)
        elif tipo_horario == "laboral":
            horarios_data = HorarioUtils.generar_horarios_laborales(cancha_id)
        else:
            raise HTTPException(status_code=400, detail="Tipo de horario no válido. Use 'completo' o 'laboral'")
        
        # Crear todas las disponibilidades
        nuevas_disponibilidades = []
        for horario_data in horarios_data:
            nueva_disponibilidad = CanchaDisponibilidad(**horario_data)
            self.db.add(nueva_disponibilidad)
            nuevas_disponibilidades.append(nueva_disponibilidad)
        
        self.db.commit()
        
        # Refrescar y retornar
        for disp in nuevas_disponibilidades:
            self.db.refresh(disp)
        
        return [CanchaDisponibilidadResponse(**disp.model_dump()) for disp in nuevas_disponibilidades]
    
    def obtener_disponibilidades_cancha(self, cancha_id: str) -> List[CanchaDisponibilidadResponse]:
        """Obtener todas las disponibilidades de una cancha"""
        stmt = select(CanchaDisponibilidad).where(CanchaDisponibilidad.cancha_id == cancha_id)
        disponibilidades = self.db.exec(stmt).all()
        
        return [CanchaDisponibilidadResponse(**disp.model_dump()) for disp in disponibilidades]
    
    def obtener_disponibilidades_dia(self, cancha_id: str, dia_semana: DiasSemana) -> List[CanchaDisponibilidadResponse]:
        """Obtener disponibilidades de una cancha para un día específico"""
        stmt = select(CanchaDisponibilidad).where(
            CanchaDisponibilidad.cancha_id == cancha_id,
            CanchaDisponibilidad.dia_semana == dia_semana
        )
        disponibilidades = self.db.exec(stmt).all()
        
        return [CanchaDisponibilidadResponse(**disp.model_dump()) for disp in disponibilidades]
    
    def actualizar_disponibilidad(self, disponibilidad_id: str, update_data: CanchaDisponibilidadUpdate) -> CanchaDisponibilidadResponse:
        """Actualizar una disponibilidad existente"""
        disponibilidad = self.db.get(CanchaDisponibilidad, disponibilidad_id)
        if not disponibilidad:
            raise HTTPException(status_code=404, detail="Disponibilidad no encontrada")
        
        # Aplicar actualizaciones
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Si se actualizan horarios, validar
        if "hora_inicio" in update_dict or "hora_fin" in update_dict:
            hora_inicio = update_dict.get("hora_inicio", disponibilidad.hora_inicio)
            hora_fin = update_dict.get("hora_fin", disponibilidad.hora_fin)
            
            if not HorarioUtils.validar_bloque_horario(hora_inicio, hora_fin):
                raise HTTPException(status_code=400, detail="El bloque debe ser de exactamente 1 hora")
        
        for key, value in update_dict.items():
            setattr(disponibilidad, key, value)
        
        disponibilidad.fecha_actualizacion = datetime.utcnow()
        self.db.commit()
        self.db.refresh(disponibilidad)
        
        return CanchaDisponibilidadResponse(**disponibilidad.model_dump())
    
    def eliminar_disponibilidad(self, disponibilidad_id: str) -> bool:
        """Eliminar una disponibilidad"""
        disponibilidad = self.db.get(CanchaDisponibilidad, disponibilidad_id)
        if not disponibilidad:
            raise HTTPException(status_code=404, detail="Disponibilidad no encontrada")
        
        self.db.delete(disponibilidad)
        self.db.commit()
        return True
    
    def cambiar_estado_bloque(self, disponibilidad_id: str, nuevo_estado: EstadoDisponibilidad) -> CanchaDisponibilidadResponse:
        """Cambiar el estado de un bloque específico"""
        disponibilidad = self.db.get(CanchaDisponibilidad, disponibilidad_id)
        if not disponibilidad:
            raise HTTPException(status_code=404, detail="Disponibilidad no encontrada")
        
        disponibilidad.estado = nuevo_estado
        disponibilidad.fecha_actualizacion = datetime.utcnow()
        self.db.commit()
        self.db.refresh(disponibilidad)
        
        return CanchaDisponibilidadResponse(**disponibilidad.model_dump())
    
    def obtener_bloques_disponibles_fecha(self, cancha_id: str, fecha: date) -> List[CanchaDisponibilidadResponse]:
        """Obtener bloques disponibles para una fecha específica"""
        dia_semana = HorarioUtils.date_to_dia_semana(fecha)
        
        stmt = select(CanchaDisponibilidad).where(
            CanchaDisponibilidad.cancha_id == cancha_id,
            CanchaDisponibilidad.dia_semana == dia_semana,
            CanchaDisponibilidad.estado == EstadoDisponibilidad.DISPONIBLE
        )
        disponibilidades = self.db.exec(stmt).all()
        
        return [CanchaDisponibilidadResponse(**disp.model_dump()) for disp in disponibilidades]
    
    def _verificar_conflicto_disponibilidad(self, cancha_id: str, dia_semana: DiasSemana, 
                                          hora_inicio, hora_fin, excluir_id: str = None) -> bool:
        """Verificar si hay conflicto con bloques existentes"""
        stmt = select(CanchaDisponibilidad).where(
            CanchaDisponibilidad.cancha_id == cancha_id,
            CanchaDisponibilidad.dia_semana == dia_semana
        )
        
        if excluir_id:
            stmt = stmt.where(CanchaDisponibilidad.disponibilidad_id != excluir_id)
        
        disponibilidades_existentes = self.db.exec(stmt).all()
        
        for disp in disponibilidades_existentes:
            if HorarioUtils.hay_conflicto_horario(hora_inicio, hora_fin, disp.hora_inicio, disp.hora_fin):
                return True
        
        return False
