from sqlmodel import Session, select
from models.reserva_model import Reserva, ReservaCreate, ReservaUpdate, UsuarioInfo
from models.cancha_model import Cancha
from schemas.reserva_schema import ReservaCreateSchema
from controllers.disponibilidad_validador import DisponibilidadValidador
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
import httpx
import os

async def create_reserva_con_snapshot(reserva_data: ReservaCreateSchema, user_id: str, session: Session, user_token: str = None) -> Reserva:

    cancha = session.get(Cancha, reserva_data.cancha_id)
    if not cancha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cancha no encontrada"
        )
    
    print(f"Cancha encontrada: {cancha.nombre}, disponible: {cancha.disponible}")
    
    if not cancha.disponible:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cancha no está disponible"
        )
    

    validador = DisponibilidadValidador(session)
    
    # Verificar configuración de la cancha
    config_valida, config_msg = validador.validar_configuracion_cancha(reserva_data.cancha_id)
    if not config_valida:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=config_msg
        )
    
    # Validar disponibilidad según bloques configurados
    es_valida, mensaje_error = validador.validar_reserva_bloques(
        reserva_data.cancha_id,
        reserva_data.fecha_inicio,
        reserva_data.fecha_fin
    )
    
    if not es_valida:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=mensaje_error
        )
    
    # Obtener datos del usuario
    user_email = None
    user_nombre = "Usuario no encontrado"
    user_telefono = None
    
    if user_token:
        try:
            user_info = await get_user_info(user_id, user_token)
            if user_info:
                user_email = user_info.email
                user_nombre = user_info.nombre_completo or user_info.username
                # El telefono no viene en UsuarioInfo, necesitaríamos obtenerlo de otra manera
                user_telefono = None
        except Exception as e:
            print(f"Error obteniendo datos del usuario con token: {e}")
    
    # Si no tenemos token o falló la consulta con token, intentar sin token
    if user_email is None:
        try:
            user_data = await get_user_data(user_id)
            user_email = user_data.get("email")
            user_nombre = f"{user_data.get('nombre', '')} {user_data.get('apellido', '')}".strip()
            if not user_nombre:
                user_nombre = user_data.get('username', 'Usuario no encontrado')
            user_telefono = user_data.get("telefono")
        except Exception as e:
            print(f"Error obteniendo datos del usuario: {e}")
            user_email = "N/A"
            user_nombre = "Error de conexión"
            user_telefono = None
    
    # Calcular precio total usando el nuevo sistema de precios por bloque
    precio_total = validador.obtener_precio_bloque(
        reserva_data.cancha_id,
        reserva_data.fecha_inicio,
        reserva_data.fecha_fin
    )
    
    # Crear la reserva con snapshot del usuario
    reserva = Reserva(
        cancha_id=reserva_data.cancha_id,
        user_id=user_id,
        fecha_inicio=reserva_data.fecha_inicio,
        fecha_fin=reserva_data.fecha_fin,
        precio_total=precio_total,
        notas=reserva_data.notas or "",
        # Snapshot del usuario
        user_email=user_email,
        user_nombre=user_nombre,
        user_telefono=user_telefono
    )
    
    session.add(reserva)
    session.commit()
    session.refresh(reserva)
    
    return reserva

def create_reserva_simple(reserva_data: ReservaCreateSchema, user_id: str, session: Session) -> Reserva:
    """Crear una nueva reserva de forma simple"""
    # Verificar que la cancha existe
    cancha = session.get(Cancha, reserva_data.cancha_id)
    if not cancha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cancha no encontrada"
        )
    
    if not cancha.disponible:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cancha no está disponible"
        )
    
    # Verificar que no haya conflictos de horario
    if check_conflicto_horario(reserva_data.cancha_id, reserva_data.fecha_inicio, reserva_data.fecha_fin, session):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una reserva en ese horario"
        )
    
    # Calcular precio total
    duration_hours = (reserva_data.fecha_fin - reserva_data.fecha_inicio).total_seconds() / 3600
    precio_total = cancha.precio_por_hora * duration_hours
    
    # Crear la reserva directamente (por ahora sin snapshot del usuario)
    # TODO: En producción, obtener datos del usuario desde auth service
    reserva = Reserva(
        cancha_id=reserva_data.cancha_id,
        user_id=user_id,
        fecha_inicio=reserva_data.fecha_inicio,
        fecha_fin=reserva_data.fecha_fin,
        precio_total=precio_total,
        notas=reserva_data.notas or "",
        # Snapshot del usuario (por ahora vacío)
        user_email=None,  # TODO: Obtener del auth service
        user_nombre=None,  # TODO: Obtener del auth service
        user_telefono=None  # TODO: Obtener del auth service
    )
    
    session.add(reserva)
    session.commit()
    session.refresh(reserva)
    
    return reserva

def create_reserva(reserva_data: ReservaCreate, user_id: str, session: Session) -> Reserva:
    """Crear una nueva reserva"""
    # Verificar que la cancha existe
    cancha = session.get(Cancha, reserva_data.cancha_id)
    if not cancha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cancha no encontrada"
        )
    
    if not cancha.disponible:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cancha no está disponible"
        )
    
    # Verificar que no haya conflictos de horario
    if check_conflicto_horario(reserva_data.cancha_id, reserva_data.fecha_inicio, reserva_data.fecha_fin, session):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una reserva en ese horario"
        )
    
    # Calcular precio total
    horas = (reserva_data.fecha_fin - reserva_data.fecha_inicio).total_seconds() / 3600
    precio_total = horas * cancha.precio_por_hora
    
    reserva = Reserva(
        cancha_id=reserva_data.cancha_id,
        user_id=user_id,
        fecha_inicio=reserva_data.fecha_inicio,
        fecha_fin=reserva_data.fecha_fin,
        precio_total=precio_total,
        estado="pendiente",
        notas=reserva_data.notas
    )
    
    session.add(reserva)
    session.commit()
    session.refresh(reserva)
    return reserva







def check_conflicto_horario(cancha_id: str, fecha_inicio: datetime, fecha_fin: datetime, session: Session) -> bool:
    """Verificar si hay conflictos de horario para una reserva"""
    statement = select(Reserva).where(
        Reserva.cancha_id == cancha_id,
        Reserva.estado != "cancelada",
        Reserva.fecha_inicio < fecha_fin,
        Reserva.fecha_fin > fecha_inicio
    )
    reservas_conflicto = session.exec(statement).all()
    return len(reservas_conflicto) > 0

def get_reservas_by_user(user_id: str, session: Session) -> List[Reserva]:
    """Obtener todas las reservas de un usuario"""
    statement = select(Reserva).where(Reserva.user_id == user_id)
    reservas = session.exec(statement).all()
    return reservas

def get_reservas_by_cancha(cancha_id: str, session: Session) -> List[Reserva]:
    """Obtener todas las reservas de una cancha"""
    statement = select(Reserva).where(Reserva.cancha_id == cancha_id)
    reservas = session.exec(statement).all()
    return reservas

def get_all_reservas(session: Session, skip: int = 0, limit: int = 100) -> List[Reserva]:
    """Obtener todas las reservas con paginación"""
    statement = select(Reserva).offset(skip).limit(limit)
    reservas = session.exec(statement).all()
    return reservas

def get_reserva_by_id(reserva_id: str, session: Session) -> Reserva:
    """Obtener una reserva por ID"""
    reserva = session.get(Reserva, reserva_id)
    if not reserva:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    return reserva

def update_reserva(reserva_id: str, reserva_data: ReservaUpdate, user_id: str, user_role: str, session: Session) -> Reserva:
    """Actualizar una reserva"""
    reserva = session.get(Reserva, reserva_id)
    if not reserva:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    # Solo el dueño de la reserva o un admin pueden modificarla
    if reserva.user_id != user_id and user_role != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar esta reserva"
        )
    
    # Si se cambian las fechas, verificar conflictos
    if reserva_data.fecha_inicio or reserva_data.fecha_fin:
        nueva_fecha_inicio = reserva_data.fecha_inicio or reserva.fecha_inicio
        nueva_fecha_fin = reserva_data.fecha_fin or reserva.fecha_fin
        
        # Verificar conflictos excluyendo la reserva actual
        statement = select(Reserva).where(
            Reserva.cancha_id == reserva.cancha_id,
            Reserva.reserva_id != reserva_id,
            Reserva.estado != "cancelada",
            Reserva.fecha_inicio < nueva_fecha_fin,
            Reserva.fecha_fin > nueva_fecha_inicio
        )
        reservas_conflicto = session.exec(statement).all()
        
        if reservas_conflicto:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una reserva en ese horario"
            )
    
    reserva_dict = reserva_data.model_dump(exclude_unset=True)
    for key, value in reserva_dict.items():
        setattr(reserva, key, value)
    
    # Recalcular precio si cambiaron las fechas
    if reserva_data.fecha_inicio or reserva_data.fecha_fin:
        cancha = session.get(Cancha, reserva.cancha_id)
        horas = (reserva.fecha_fin - reserva.fecha_inicio).total_seconds() / 3600
        reserva.precio_total = horas * cancha.precio_por_hora
    
    reserva.fecha_actualizacion = datetime.utcnow()
    session.add(reserva)
    session.commit()
    session.refresh(reserva)
    return reserva

def cancel_reserva(reserva_id: str, user_id: str, user_role: str, session: Session) -> Reserva:
    """Cancelar una reserva"""
    reserva = session.get(Reserva, reserva_id)
    if not reserva:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    # Solo el dueño de la reserva o un admin pueden cancelarla
    if reserva.user_id != user_id and user_role != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para cancelar esta reserva"
        )
    
    if reserva.estado == "cancelada":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La reserva ya está cancelada"
        )
    
    reserva.estado = "cancelada"
    reserva.fecha_actualizacion = datetime.utcnow()
    session.add(reserva)
    session.commit()
    session.refresh(reserva)
    return reserva

async def get_user_info(user_id: str, token: str) -> Optional[UsuarioInfo]:
    """Obtener información del usuario desde el servicio de autenticación"""
    try:
        auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{auth_service_url}/auth/user/{user_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Datos obtenidos del auth service (get_user_info): {user_data}")
                return UsuarioInfo(
                    user_id=user_data.get("uid"),  # Cambiado de user_id a uid
                    username=user_data.get("username"),
                    email=user_data.get("email"),
                    nombre_completo=user_data.get("last_name")  # Usar last_name como nombre completo temporalmente
                )
            else:
                print(f"❌ Error del auth service (get_user_info): {response.status_code}")
    except Exception as e:
        print(f"❌ Error obteniendo información del usuario: {e}")
        return None
    
    return None

async def get_user_data(user_id: str):
    """Obtener datos del usuario desde el auth service"""
    try:
        auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
        async with httpx.AsyncClient() as client:
            # Usar el endpoint real del servicio de auth
            response = await client.get(f"{auth_service_url}/auth/user/{user_id}")
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Datos obtenidos del auth service: {user_data}")
                return {
                    "email": user_data.get("email", ""),
                    "nombre": user_data.get("username", ""),
                    "apellido": user_data.get("last_name", ""),
                    "telefono": "N/A",  # El auth service no tiene teléfono aún
                    "username": user_data.get("username", "")
                }
            else:
                print(f"❌ Error del auth service: {response.status_code}")
                raise Exception(f"Auth service error: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error obteniendo usuario: {e}")
        print("📝 Usando datos de fallback")
        
        # Fallback a datos conocidos para testing
        fallback_data = {
            "597780ce-f6d3-4ace-a30e-57aef1bf3fe0": {
                "email": "testuser456@example.com",
                "nombre": "TestUser456",
                "apellido": "User",
                "telefono": "+0987654321",
                "username": "testuser456"
            },
            "04f00257-4446-49e2-b933-24be81d4a405": {
                "email": "marcos@example.com",
                "nombre": "Marcos",
                "apellido": "González",
                "telefono": "+1234567890",
                "username": "marcos"
            }
        }
        
        return fallback_data.get(user_id, {
            "email": "usuario@example.com", 
            "nombre": "Usuario", 
            "apellido": "Desconocido",
            "telefono": "0000000000",
            "username": "usuario_desconocido"
        })

async def get_reserva_completa(reserva_id: str, session: Session):
    """Obtener reserva con datos de usuario y cancha"""
    # 1. Obtener la reserva
    reserva = session.exec(select(Reserva).where(Reserva.reserva_id == reserva_id)).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    # 2. Obtener la cancha
    cancha = session.exec(select(Cancha).where(Cancha.cancha_id == reserva.cancha_id)).first()
    
    # 3. Obtener datos del usuario
    usuario_data = await get_user_data(reserva.user_id)
    
    # 4. Devolver todo junto
    return {
        "reserva_id": reserva.reserva_id,
        "fecha_inicio": reserva.fecha_inicio,
        "fecha_fin": reserva.fecha_fin,
        "precio_total": reserva.precio_total,
        "estado": reserva.estado,
        "notas": reserva.notas,
        "fecha_creacion": reserva.fecha_creacion,
        "fecha_actualizacion": reserva.fecha_actualizacion,
        
        # Datos del usuario
        "usuario": {
            "user_id": reserva.user_id,
            "username": usuario_data.get("username", "N/A"),
            "email": usuario_data.get("email", "N/A"),
            "last_name": usuario_data.get("last_name", "N/A")
        },
        
        # Datos de la cancha
        "cancha": {
            "cancha_id": cancha.cancha_id if cancha else reserva.cancha_id,
            "nombre": cancha.nombre if cancha else "Cancha no encontrada",
            "tipo_deporte": cancha.tipo_deporte if cancha else "N/A",
            "ubicacion": cancha.ubicacion if cancha else "N/A", 
            "precio_por_hora": float(cancha.precio_por_hora) if cancha else 0
        }
    }
