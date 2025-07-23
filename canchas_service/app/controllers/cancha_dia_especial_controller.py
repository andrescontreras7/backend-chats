from sqlmodel import Session, select
from models.cancha_dia_especial_model import (
    CanchaDiaEspecial, CanchaDiaEspecialCreate, CanchaDiaEspecialUpdate,
    CanchaDiaEspecialResponse, TipoDiaEspecial, EstadoDiaEspecial
)
from models.cancha_model import Cancha
from datetime import datetime, date
from typing import List, Optional
from fastapi import HTTPException

class CanchaDiaEspecialController:
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear_dia_especial(self, dia_especial_data: CanchaDiaEspecialCreate, usuario_id: str = None) -> CanchaDiaEspecialResponse:
        """Crear un día especial para una cancha"""
        
        # Verificar que la cancha existe
        cancha = self.db.get(Cancha, dia_especial_data.cancha_id)
        if not cancha:
            raise HTTPException(status_code=404, detail="Cancha no encontrada")
        
        # Verificar que no existe ya un día especial para esta fecha
        stmt = select(CanchaDiaEspecial).where(
            CanchaDiaEspecial.cancha_id == dia_especial_data.cancha_id,
            CanchaDiaEspecial.fecha == dia_especial_data.fecha
        )
        dia_existente = self.db.exec(stmt).first()
        if dia_existente:
            raise HTTPException(status_code=400, detail="Ya existe un día especial configurado para esta fecha")
        
        # Validar horarios si es horario especial
        if dia_especial_data.estado == EstadoDiaEspecial.HORARIO_ESPECIAL:
            if not dia_especial_data.hora_inicio or not dia_especial_data.hora_fin:
                raise HTTPException(status_code=400, detail="Para horario especial debe especificar hora_inicio y hora_fin")
            
            if dia_especial_data.hora_inicio >= dia_especial_data.hora_fin:
                raise HTTPException(status_code=400, detail="La hora de inicio debe ser menor que la hora de fin")
        
        # Crear el día especial
        nuevo_dia_especial = CanchaDiaEspecial(**dia_especial_data.model_dump())
        if usuario_id:
            nuevo_dia_especial.creado_por = usuario_id
        
        self.db.add(nuevo_dia_especial)
        self.db.commit()
        self.db.refresh(nuevo_dia_especial)
        
        return CanchaDiaEspecialResponse(**nuevo_dia_especial.model_dump())
    
    def obtener_dias_especiales_cancha(self, cancha_id: str, fecha_desde: date = None, fecha_hasta: date = None) -> List[CanchaDiaEspecialResponse]:
        """Obtener días especiales de una cancha, opcionalmente filtrados por rango de fechas"""
        stmt = select(CanchaDiaEspecial).where(CanchaDiaEspecial.cancha_id == cancha_id)
        
        if fecha_desde:
            stmt = stmt.where(CanchaDiaEspecial.fecha >= fecha_desde)
        if fecha_hasta:
            stmt = stmt.where(CanchaDiaEspecial.fecha <= fecha_hasta)
        
        stmt = stmt.order_by(CanchaDiaEspecial.fecha)
        dias_especiales = self.db.exec(stmt).all()
        
        return [CanchaDiaEspecialResponse(**dia.model_dump()) for dia in dias_especiales]
    
    def obtener_dia_especial_fecha(self, cancha_id: str, fecha: date) -> Optional[CanchaDiaEspecialResponse]:
        """Obtener día especial para una fecha específica"""
        stmt = select(CanchaDiaEspecial).where(
            CanchaDiaEspecial.cancha_id == cancha_id,
            CanchaDiaEspecial.fecha == fecha
        )
        dia_especial = self.db.exec(stmt).first()
        
        if dia_especial:
            return CanchaDiaEspecialResponse(**dia_especial.model_dump())
        return None
    
    def actualizar_dia_especial(self, dia_especial_id: str, update_data: CanchaDiaEspecialUpdate) -> CanchaDiaEspecialResponse:
        """Actualizar un día especial existente"""
        dia_especial = self.db.get(CanchaDiaEspecial, dia_especial_id)
        if not dia_especial:
            raise HTTPException(status_code=404, detail="Día especial no encontrado")
        
        # Aplicar actualizaciones
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Validar horarios si se actualiza a horario especial
        estado_actualizado = update_dict.get("estado", dia_especial.estado)
        if estado_actualizado == EstadoDiaEspecial.HORARIO_ESPECIAL:
            hora_inicio = update_dict.get("hora_inicio", dia_especial.hora_inicio)
            hora_fin = update_dict.get("hora_fin", dia_especial.hora_fin)
            
            if not hora_inicio or not hora_fin:
                raise HTTPException(status_code=400, detail="Para horario especial debe especificar hora_inicio y hora_fin")
            
            if hora_inicio >= hora_fin:
                raise HTTPException(status_code=400, detail="La hora de inicio debe ser menor que la hora de fin")
        
        for key, value in update_dict.items():
            setattr(dia_especial, key, value)
        
        dia_especial.fecha_actualizacion = datetime.utcnow()
        self.db.commit()
        self.db.refresh(dia_especial)
        
        return CanchaDiaEspecialResponse(**dia_especial.model_dump())
    
    def eliminar_dia_especial(self, dia_especial_id: str) -> bool:
        """Eliminar un día especial"""
        dia_especial = self.db.get(CanchaDiaEspecial, dia_especial_id)
        if not dia_especial:
            raise HTTPException(status_code=404, detail="Día especial no encontrado")
        
        self.db.delete(dia_especial)
        self.db.commit()
        return True
    
    def crear_feriados_anuales(self, cancha_id: str, year: int, feriados_data: List[CanchaDiaEspecialCreate]) -> List[CanchaDiaEspecialResponse]:
        """Crear múltiples feriados para un año específico"""
        
        # Verificar que la cancha existe
        cancha = self.db.get(Cancha, cancha_id)
        if not cancha:
            raise HTTPException(status_code=404, detail="Cancha no encontrada")
        
        # Eliminar feriados existentes para este año
        stmt = select(CanchaDiaEspecial).where(
            CanchaDiaEspecial.cancha_id == cancha_id,
            CanchaDiaEspecial.tipo == TipoDiaEspecial.FERIADO
        )
        feriados_existentes = self.db.exec(stmt).all()
        
        for feriado in feriados_existentes:
            if feriado.fecha.year == year:
                self.db.delete(feriado)
        
        # Crear nuevos feriados
        nuevos_feriados = []
        for feriado_data in feriados_data:
            if feriado_data.fecha.year != year:
                raise HTTPException(status_code=400, detail=f"Todos los feriados deben ser del año {year}")
            
            nuevo_feriado = CanchaDiaEspecial(**feriado_data.model_dump())
            nuevo_feriado.cancha_id = cancha_id
            nuevo_feriado.tipo = TipoDiaEspecial.FERIADO
            
            self.db.add(nuevo_feriado)
            nuevos_feriados.append(nuevo_feriado)
        
        self.db.commit()
        
        # Refrescar y retornar
        for feriado in nuevos_feriados:
            self.db.refresh(feriado)
        
        return [CanchaDiaEspecialResponse(**feriado.model_dump()) for feriado in nuevos_feriados]
    
    def obtener_feriados_mes(self, cancha_id: str, year: int, month: int) -> List[CanchaDiaEspecialResponse]:
        """Obtener feriados de un mes específico"""
        stmt = select(CanchaDiaEspecial).where(
            CanchaDiaEspecial.cancha_id == cancha_id,
            CanchaDiaEspecial.tipo == TipoDiaEspecial.FERIADO
        )
        
        todos_feriados = self.db.exec(stmt).all()
        
        # Filtrar por año y mes
        feriados_mes = [
            feriado for feriado in todos_feriados
            if feriado.fecha.year == year and feriado.fecha.month == month
        ]
        
        return [CanchaDiaEspecialResponse(**feriado.model_dump()) for feriado in feriados_mes]
    
    def marcar_mantenimiento(self, cancha_id: str, fecha_inicio: date, fecha_fin: date, descripcion: str) -> List[CanchaDiaEspecialResponse]:
        """Marcar días de mantenimiento para un rango de fechas"""
        
        # Verificar que la cancha existe
        cancha = self.db.get(Cancha, cancha_id)
        if not cancha:
            raise HTTPException(status_code=404, detail="Cancha no encontrada")
        
        if fecha_inicio > fecha_fin:
            raise HTTPException(status_code=400, detail="La fecha de inicio debe ser menor o igual a la fecha de fin")
        
        # Crear días de mantenimiento
        dias_mantenimiento = []
        fecha_actual = fecha_inicio
        
        while fecha_actual <= fecha_fin:
            # Verificar si ya existe un día especial para esta fecha
            stmt = select(CanchaDiaEspecial).where(
                CanchaDiaEspecial.cancha_id == cancha_id,
                CanchaDiaEspecial.fecha == fecha_actual
            )
            dia_existente = self.db.exec(stmt).first()
            
            if dia_existente:
                # Actualizar día existente
                dia_existente.tipo = TipoDiaEspecial.MANTENIMIENTO
                dia_existente.estado = EstadoDiaEspecial.CERRADO
                dia_existente.descripcion = descripcion
                dia_existente.fecha_actualizacion = datetime.utcnow()
                dias_mantenimiento.append(dia_existente)
            else:
                # Crear nuevo día de mantenimiento
                nuevo_dia = CanchaDiaEspecial(
                    cancha_id=cancha_id,
                    fecha=fecha_actual,
                    tipo=TipoDiaEspecial.MANTENIMIENTO,
                    estado=EstadoDiaEspecial.CERRADO,
                    descripcion=descripcion
                )
                self.db.add(nuevo_dia)
                dias_mantenimiento.append(nuevo_dia)
            
            fecha_actual += date.resolution  # Incrementar un día
        
        self.db.commit()
        
        # Refrescar todos los días
        for dia in dias_mantenimiento:
            self.db.refresh(dia)
        
        return [CanchaDiaEspecialResponse(**dia.model_dump()) for dia in dias_mantenimiento]
