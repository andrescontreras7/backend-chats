from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import Session
from database import get_session
from schemas.reserva_schema import ReservaSchema, ReservaCreateSchema, ReservaUpdateSchema
from controllers.reserva_controller import (
    create_reserva, get_reservas_by_user, get_reservas_by_cancha, 
    get_all_reservas, get_reserva_by_id, update_reserva, cancel_reserva, 
    get_user_info, create_reserva_con_snapshot
)
from models.reserva_model import ReservaCreate, ReservaUpdate, ReservaConUsuario
from auth.auth_middleware import require_admin, get_current_user
from typing import List

router = APIRouter()

@router.post("/create", response_model=ReservaSchema)
async def create_reserva_route(
    reserva_data: ReservaCreateSchema,
    request: Request,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Crear una nueva reserva."""
    # Extraer token del header Authorization
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    # Usar la función con snapshot de usuario
    from controllers.reserva_controller import create_reserva_con_snapshot
    return await create_reserva_con_snapshot(reserva_data, current_user["user_id"], session, token)

@router.get("/", response_model=List[ReservaSchema])
def get_all_reservas_route(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver"),
    session: Session = Depends(get_session),
    admin_user: dict = Depends(require_admin)
):
    """Obtener todas las reservas. Solo administradores."""
    return get_all_reservas(session, skip, limit)

@router.get("/with-users", response_model=List[ReservaConUsuario])
async def get_all_reservas_with_users_route(
    request: Request,
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver"),
    session: Session = Depends(get_session),
    admin_user: dict = Depends(require_admin)
):
    """Obtener todas las reservas con información de usuarios. Solo administradores."""
    reservas = get_all_reservas(session, skip, limit)
    
    # Obtener token del header Authorization
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    reservas_con_usuarios = []
    for reserva in reservas:
        reserva_response = ReservaConUsuario(
            cancha_id=reserva.cancha_id,
            fecha_inicio=reserva.fecha_inicio,
            fecha_fin=reserva.fecha_fin,
            estado=reserva.estado,
            notas=reserva.notas,
            reserva_id=reserva.reserva_id,
            user_id=reserva.user_id,
            precio_total=reserva.precio_total,
            fecha_creacion=reserva.fecha_creacion,
            fecha_actualizacion=reserva.fecha_actualizacion
        )
        
        # Intentar obtener información del usuario
        if token:
            user_info = await get_user_info(reserva.user_id, token)
            reserva_response.usuario = user_info
        
        reservas_con_usuarios.append(reserva_response)
    
    return reservas_con_usuarios

@router.get("/mis-reservas", response_model=List[ReservaSchema])
def get_mis_reservas_route(
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Obtener las reservas del usuario actual."""
    return get_reservas_by_user(current_user["user_id"], session)

@router.get("/cancha/{cancha_id}", response_model=List[ReservaSchema])
def get_reservas_by_cancha_route(
    cancha_id: str,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
 
    return get_reservas_by_cancha(cancha_id, session)

@router.get("/{reserva_id}", response_model=ReservaSchema)
def get_reserva_route(
    reserva_id: str,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Obtener una reserva específica por ID."""
    reserva = get_reserva_by_id(reserva_id, session)
    
    # Solo el dueño de la reserva o un admin pueden verla
    if reserva.user_id != current_user["user_id"] and current_user["role"] != "administrador":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver esta reserva"
        )
    
    return reserva

@router.get("/{reserva_id}/with-user", response_model=ReservaConUsuario)
async def get_reserva_with_user_route(
    reserva_id: str,
    request: Request,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Obtener una reserva específica con información completa del usuario."""
    reserva = get_reserva_by_id(reserva_id, session)
    
    # Solo el dueño de la reserva o un admin pueden verla
    if reserva.user_id != current_user["user_id"] and current_user["role"] != "administrador":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver esta reserva"
        )
    
    # Obtener token del header Authorization
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    # Crear respuesta base
    reserva_response = ReservaConUsuario(
        cancha_id=reserva.cancha_id,
        fecha_inicio=reserva.fecha_inicio,
        fecha_fin=reserva.fecha_fin,
        estado=reserva.estado,
        notas=reserva.notas,
        reserva_id=reserva.reserva_id,
        user_id=reserva.user_id,
        precio_total=reserva.precio_total,
        fecha_creacion=reserva.fecha_creacion,
        fecha_actualizacion=reserva.fecha_actualizacion
    )
    
    # Intentar obtener información del usuario
    if token:
        user_info = await get_user_info(reserva.user_id, token)
        reserva_response.usuario = user_info
    
    return reserva_response

@router.put("/{reserva_id}", response_model=ReservaSchema)
def update_reserva_route(
    reserva_id: str,
    reserva_data: ReservaUpdateSchema,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Actualizar una reserva."""
    reserva_update = ReservaUpdate(**reserva_data.model_dump(exclude_unset=True))
    return update_reserva(
        reserva_id, 
        reserva_update, 
        current_user["user_id"], 
        current_user["role"], 
        session
    )

@router.put("/{reserva_id}/cancel", response_model=ReservaSchema)
def cancel_reserva_route(
    reserva_id: str,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Cancelar una reserva."""
    return cancel_reserva(
        reserva_id, 
        current_user["user_id"], 
        current_user["role"], 
        session
    )

@router.get("/{reserva_id}/completa")
async def get_reserva_completa_route(
    reserva_id: str,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Obtener reserva con datos completos de usuario y cancha"""
    from controllers.reserva_controller import get_reserva_completa
    return await get_reserva_completa(reserva_id, session)
