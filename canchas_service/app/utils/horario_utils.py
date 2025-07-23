from datetime import time, datetime, timedelta, date
from typing import List, Tuple
from models.cancha_disponibilidad_model import DiasSemana, EstadoDisponibilidad

class HorarioUtils:
    """Utilidades para manejar horarios y bloques de tiempo"""
    
    # Horarios estándar por defecto (bloques de 1 hora de 6:00 a 23:00)
    HORARIOS_ESTANDAR = [
        (time(6, 0), time(7, 0)),
        (time(7, 0), time(8, 0)),
        (time(8, 0), time(9, 0)),
        (time(9, 0), time(10, 0)),
        (time(10, 0), time(11, 0)),
        (time(11, 0), time(12, 0)),
        (time(12, 0), time(13, 0)),
        (time(13, 0), time(14, 0)),
        (time(14, 0), time(15, 0)),
        (time(15, 0), time(16, 0)),
        (time(16, 0), time(17, 0)),
        (time(17, 0), time(18, 0)),
        (time(18, 0), time(19, 0)),
        (time(19, 0), time(20, 0)),
        (time(20, 0), time(21, 0)),
        (time(21, 0), time(22, 0)),
        (time(22, 0), time(23, 0)),
    ]
    
    @staticmethod
    def datetime_to_dia_semana(fecha: datetime) -> DiasSemana:
        """Convierte un datetime a DiasSemana enum"""
        dias = {
            0: DiasSemana.LUNES,
            1: DiasSemana.MARTES,
            2: DiasSemana.MIERCOLES,
            3: DiasSemana.JUEVES,
            4: DiasSemana.VIERNES,
            5: DiasSemana.SABADO,
            6: DiasSemana.DOMINGO,
        }
        return dias[fecha.weekday()]
    
    @staticmethod
    def date_to_dia_semana(fecha: date) -> DiasSemana:
        """Convierte un date a DiasSemana enum"""
        return HorarioUtils.datetime_to_dia_semana(datetime.combine(fecha, time()))
    
    @staticmethod
    def generar_horarios_semana_completa(cancha_id: str) -> List[dict]:
        """Genera horarios estándar para toda la semana"""
        horarios = []
        
        for dia in DiasSemana:
            for hora_inicio, hora_fin in HorarioUtils.HORARIOS_ESTANDAR:
                horarios.append({
                    "cancha_id": cancha_id,
                    "dia_semana": dia,
                    "hora_inicio": hora_inicio,
                    "hora_fin": hora_fin,
                    "estado": EstadoDisponibilidad.DISPONIBLE
                })
        
        return horarios
    
    @staticmethod
    def generar_horarios_laborales(cancha_id: str) -> List[dict]:
        """Genera horarios solo de lunes a viernes de 8:00 a 18:00"""
        horarios = []
        dias_laborales = [DiasSemana.LUNES, DiasSemana.MARTES, DiasSemana.MIERCOLES, 
                         DiasSemana.JUEVES, DiasSemana.VIERNES]
        
        horarios_laborales = [
            (time(8, 0), time(9, 0)),
            (time(9, 0), time(10, 0)),
            (time(10, 0), time(11, 0)),
            (time(11, 0), time(12, 0)),
            (time(12, 0), time(13, 0)),
            (time(13, 0), time(14, 0)),
            (time(14, 0), time(15, 0)),
            (time(15, 0), time(16, 0)),
            (time(16, 0), time(17, 0)),
            (time(17, 0), time(18, 0)),
        ]
        
        for dia in dias_laborales:
            for hora_inicio, hora_fin in horarios_laborales:
                horarios.append({
                    "cancha_id": cancha_id,
                    "dia_semana": dia,
                    "hora_inicio": hora_inicio,
                    "hora_fin": hora_fin,
                    "estado": EstadoDisponibilidad.DISPONIBLE
                })
        
        return horarios
    
    @staticmethod
    def validar_bloque_horario(hora_inicio: time, hora_fin: time) -> bool:
        """Valida que un bloque horario sea válido (1 hora exacta)"""
        # Convertir a datetime para hacer cálculos
        dt_inicio = datetime.combine(date.today(), hora_inicio)
        dt_fin = datetime.combine(date.today(), hora_fin)
        
        # Verificar que la diferencia sea exactamente 1 hora
        diferencia = dt_fin - dt_inicio
        return diferencia == timedelta(hours=1)
    
    @staticmethod
    def hay_conflicto_horario(hora_inicio_1: time, hora_fin_1: time, 
                             hora_inicio_2: time, hora_fin_2: time) -> bool:
        """Verifica si dos bloques horarios se superponen"""
        # Convertir a datetime para comparar
        dt1_inicio = datetime.combine(date.today(), hora_inicio_1)
        dt1_fin = datetime.combine(date.today(), hora_fin_1)
        dt2_inicio = datetime.combine(date.today(), hora_inicio_2)
        dt2_fin = datetime.combine(date.today(), hora_fin_2)
        
        # Verificar superposición
        return not (dt1_fin <= dt2_inicio or dt2_fin <= dt1_inicio)
    
    @staticmethod
    def convertir_datetime_a_bloque(fecha_inicio: datetime, fecha_fin: datetime) -> Tuple[date, time, time]:
        """Convierte datetime de reserva a fecha, hora_inicio y hora_fin para bloques"""
        fecha = fecha_inicio.date()
        hora_inicio = fecha_inicio.time()
        hora_fin = fecha_fin.time()
        
        return fecha, hora_inicio, hora_fin
    
    @staticmethod
    def es_horario_valido_reserva(fecha_inicio: datetime, fecha_fin: datetime) -> bool:
        """Valida que una reserva sea exactamente de 1 hora y en horario permitido"""
        diferencia = fecha_fin - fecha_inicio
        print(f"⏰ Diferencia de tiempo: {diferencia}")
        
        # Debe ser exactamente 1 hora
        if diferencia != timedelta(hours=1):
            print("⏰ Error: La diferencia NO es exactamente 1 hora")
            return False
        
        # La hora debe estar en los bloques estándar
        hora_inicio = fecha_inicio.time()
        hora_fin = fecha_fin.time()
        
        bloque_encontrado = (hora_inicio, hora_fin) in HorarioUtils.HORARIOS_ESTANDAR
        if not bloque_encontrado:
            print(f"⏰ Error: El bloque {hora_inicio}-{hora_fin} NO está en los bloques estándar")
            primeros_bloques = [(h1.strftime('%H:%M'), h2.strftime('%H:%M')) for h1, h2 in HorarioUtils.HORARIOS_ESTANDAR[:3]]
            print(f"⏰ Bloques válidos (primeros 3): {primeros_bloques}...")
        
        return bloque_encontrado
